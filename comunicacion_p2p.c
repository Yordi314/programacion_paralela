#include <stdio.h>
#include <mpi.h>

int main(int argc, char** argv) {
    int rank, size, dato;
    MPI_Status estado;

    MPI_Init(&argc, &argv);
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    if (size < 2) {
        if (rank == 0) {
            printf("Error: este programa requiere al menos 2 procesos.\n");
        }
        MPI_Finalize();
        return 1;
    }

    if (rank == 0) {
        dato = 100;
        MPI_Send(&dato, 1, MPI_INT, 1, 0, MPI_COMM_WORLD);
        printf("Proceso 0: envie el valor %d al proceso 1.\n", dato);
    } else if (rank == 1) {
        MPI_Recv(&dato, 1, MPI_INT, 0, 0, MPI_COMM_WORLD, &estado);
        printf("Proceso 1: recibi el valor %d enviado por el proceso %d.\n",
               dato, estado.MPI_SOURCE);
    }

    MPI_Finalize();
    return 0;
}
