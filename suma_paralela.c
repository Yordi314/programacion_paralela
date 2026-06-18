/* =============================================================================
 *  suma_paralela.c
 *  Suma de un arreglo de enteros usando OpenMP.
 *
 *  Calcula la suma de un arreglo grande paralelizando el bucle con una
 *  reduccion de OpenMP, y mide el tiempo de ejecucion para un numero dado
 *  de hilos. Pensado para estudiar speedup, eficiencia, escalabilidad y la
 *  Ley de Amdahl variando la cantidad de hilos.
 *
 *  Compilacion:
 *      gcc -O2 -fopenmp suma_paralela.c -o suma_paralela
 *
 *  Uso:
 *      ./suma_paralela <N> <hilos> [repeticiones]
 *      Ej.:  ./suma_paralela 100000000 4 5
 *
 *  Salida (linea CSV):  hilos,tiempo_s,suma
 *  El campo 'suma' debe ser identico para todo numero de hilos: sirve de
 *  verificacion de correctitud (la reduccion no debe alterar el resultado).
 * ========================================================================== */

#include <stdio.h>
#include <stdlib.h>
#include <omp.h>

int main(int argc, char **argv) {
    long long N   = (argc > 1) ? atoll(argv[1]) : 100000000LL; /* tamano del arreglo */
    int hilos     = (argc > 2) ? atoi(argv[2])  : 1;           /* numero de hilos    */
    int repes     = (argc > 3) ? atoi(argv[3])  : 5;           /* repeticiones       */

    omp_set_num_threads(hilos);

    /* Reserva e inicializacion del arreglo.
     * Valores deterministas y acotados para evitar desbordamiento y permitir
     * reproducir el resultado. */
    int *a = (int *) malloc((size_t)N * sizeof(int));
    if (!a) { fprintf(stderr, "Error: memoria insuficiente para N=%lld\n", N); return 1; }

    #pragma omp parallel for schedule(static)
    for (long long i = 0; i < N; ++i)
        a[i] = (int)(i % 7);     /* patron repetitivo y acotado */

    /* Se ejecuta varias veces y se conserva el menor tiempo, para reducir el
     * efecto del ruido del sistema operativo en la medicion. */
    double mejor = 1e30;
    long long suma_final = 0;

    for (int r = 0; r < repes; ++r) {
        long long suma = 0;
        double t0 = omp_get_wtime();

        /* --- Region paralela ---
         * 'reduction(+:suma)' crea una copia privada de 'suma' por hilo, cada
         * hilo acumula su parte y al final OpenMP combina todas las copias de
         * forma segura. Asi se evita por completo la condicion de carrera que
         * existiria si todos los hilos escribieran sobre la misma variable. */
        #pragma omp parallel for reduction(+:suma) schedule(static)
        for (long long i = 0; i < N; ++i)
            suma += a[i];

        double t = omp_get_wtime() - t0;
        if (t < mejor) mejor = t;
        suma_final = suma;
    }

    /* Linea CSV: hilos,tiempo,suma */
    printf("%d,%.6f,%lld\n", hilos, mejor, suma_final);

    free(a);
    return 0;
}
