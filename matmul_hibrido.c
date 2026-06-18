/* =============================================================================
 *  matmul_hibrido.c
 *  Multiplicacion de matrices C = A x B con enfoque HIBRIDO MPI + OpenMP.
 *
 *  - MPI   : reparte las filas de A entre los procesos (MPI_Scatter),
 *            difunde B completa (MPI_Bcast) y recolecta C (MPI_Gather).
 *  - OpenMP: dentro de cada proceso, paraleliza el calculo de su bloque
 *            de filas usando varios hilos.
 *
 *  Compilacion:
 *      mpicc -O3 -fopenmp matmul_hibrido.c -o matmul_hibrido
 *
 *  Ejecucion:
 *      OMP_NUM_THREADS=4 mpirun -np 4 ./matmul_hibrido 1024
 *      ./matmul_hibrido <N> [hilos] [verificar(0|1)]
 *
 *  Salida (linea CSV apta para el script de benchmark):
 *      N,procesos,hilos,tiempo_total_s,tiempo_computo_s,gflops,verificacion
 *
 *  Restriccion de diseno: N debe ser divisible entre el numero de procesos,
 *  ya que MPI_Scatter reparte bloques de filas de tamano identico. El programa
 *  aborta de forma controlada si no se cumple (ver "posibles mejoras": Scatterv).
 * ========================================================================== */

#include <mpi.h>
#include <omp.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

/* Inicializacion determinista: permite reproducir resultados y verificar.
 * Valores acotados para evitar magnitudes que arruinen la comparacion. */
static void inicializar(double *M, int filas, int cols, int semilla) {
    for (int i = 0; i < filas; ++i)
        for (int j = 0; j < cols; ++j)
            M[i * cols + j] = (double)(((i + j + semilla) % 13) - 6) * 0.5;
}

/* Multiplicacion serial de referencia (solo para verificar correctitud
 * cuando N es pequeno). Orden i-k-j por localidad de cache. */
static void multiplicar_serial(const double *A, const double *B, double *C,
                               int N) {
    memset(C, 0, (size_t)N * N * sizeof(double));
    for (int i = 0; i < N; ++i)
        for (int k = 0; k < N; ++k) {
            double a = A[i * N + k];
            for (int j = 0; j < N; ++j)
                C[i * N + j] += a * B[k * N + j];
        }
}

int main(int argc, char **argv) {
    MPI_Init(&argc, &argv);

    int rank, size;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);   /* identificador del proceso */
    MPI_Comm_size(MPI_COMM_WORLD, &size);   /* numero total de procesos  */

    /* ---- Argumentos ---- */
    int N        = (argc > 1) ? atoi(argv[1]) : 1024;
    int hilos    = (argc > 2) ? atoi(argv[2]) : 0;   /* 0 => usa OMP_NUM_THREADS */
    int verifica = (argc > 3) ? atoi(argv[3]) : 0;

    if (hilos > 0) omp_set_num_threads(hilos);
    int hilos_reales = 0;
    #pragma omp parallel
    { 
        #pragma omp single
        hilos_reales = omp_get_num_threads();
    }

    /* ---- Validacion: N divisible entre size ---- */
    if (N % size != 0) {
        if (rank == 0)
            fprintf(stderr,
                "ERROR: N=%d no es divisible entre %d procesos. "
                "Use un N multiplo del numero de procesos.\n", N, size);
        MPI_Abort(MPI_COMM_WORLD, 1);
    }

    int filas_locales = N / size;          /* bloque de filas por proceso */

    /* ---- Reserva de memoria ----
     * Solo el root mantiene A y C completas (origen de Scatter / destino de Gather).
     * Todos los procesos necesitan B completa y sus buffers locales. */
    double *A = NULL, *C = NULL, *C_ref = NULL;
    double *B        = malloc((size_t)N * N * sizeof(double));
    double *A_local  = malloc((size_t)filas_locales * N * sizeof(double));
    double *C_local  = malloc((size_t)filas_locales * N * sizeof(double));

    if (rank == 0) {
        A = malloc((size_t)N * N * sizeof(double));
        C = malloc((size_t)N * N * sizeof(double));
        inicializar(A, N, N, 0);
        inicializar(B, N, N, 7);
    }

    /* ---- Distribucion de datos ----
     * B es necesaria completa en todos los procesos -> Bcast.
     * A se reparte por bloques de filas contiguas -> Scatter. */
    MPI_Bcast(B, N * N, MPI_DOUBLE, 0, MPI_COMM_WORLD);

    MPI_Barrier(MPI_COMM_WORLD);
    double t_inicio = MPI_Wtime();         /* cronometro TOTAL (incluye comunicacion) */

    MPI_Scatter(A, filas_locales * N, MPI_DOUBLE,
                A_local, filas_locales * N, MPI_DOUBLE,
                0, MPI_COMM_WORLD);

    /* ---- Calculo paralelo con OpenMP ----
     * Cada hilo procesa filas DISTINTAS de C_local: las escrituras nunca
     * coinciden en la misma direccion -> no hay condiciones de carrera y
     * no se requieren secciones criticas ni reducciones. */
    memset(C_local, 0, (size_t)filas_locales * N * sizeof(double));

    double t_comp_ini = MPI_Wtime();
    #pragma omp parallel for schedule(static)
    for (int i = 0; i < filas_locales; ++i) {
        for (int k = 0; k < N; ++k) {
            double a = A_local[i * N + k];
            for (int j = 0; j < N; ++j)
                C_local[i * N + j] += a * B[k * N + j];
        }
    }
    double t_comp = MPI_Wtime() - t_comp_ini;

    /* ---- Recoleccion de resultados ---- */
    MPI_Gather(C_local, filas_locales * N, MPI_DOUBLE,
               C, filas_locales * N, MPI_DOUBLE,
               0, MPI_COMM_WORLD);

    MPI_Barrier(MPI_COMM_WORLD);
    double t_total = MPI_Wtime() - t_inicio;

    /* El tiempo de computo reportado es el maximo entre procesos (el cuello
     * de botella real del paso paralelo). */
    double t_comp_max;
    MPI_Reduce(&t_comp, &t_comp_max, 1, MPI_DOUBLE, MPI_MAX, 0, MPI_COMM_WORLD);

    /* ---- Verificacion opcional (solo en root, N pequeno) ---- */
    int ok = -1; /* -1 = no verificado */
    if (rank == 0 && verifica) {
        C_ref = malloc((size_t)N * N * sizeof(double));
        multiplicar_serial(A, B, C_ref, N);
        ok = 1;
        for (size_t idx = 0; idx < (size_t)N * N; ++idx)
            if (fabs(C[idx] - C_ref[idx]) > 1e-9) { ok = 0; break; }
        free(C_ref);
    }

    /* ---- Reporte (root) ---- */
    if (rank == 0) {
        double ops    = 2.0 * (double)N * N * N;  /* multiplicaciones + sumas */
        double gflops = (t_comp_max > 0) ? ops / t_comp_max / 1e9 : 0.0;
        printf("%d,%d,%d,%.6f,%.6f,%.3f,%d\n",
               N, size, hilos_reales, t_total, t_comp_max, gflops, ok);
    }

    free(A); free(B); free(C);
    free(A_local); free(C_local);
    MPI_Finalize();
    return 0;
}
