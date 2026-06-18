# Makefile - Multiplicacion de matrices hibrida MPI + OpenMP
# Uso:
#   make           -> compila ./matmul_hibrido
#   make verificar -> compila y corre una prueba de correctitud (N=240, 4x2)
#   make clean     -> borra binarios y resultados

CC      = mpicc
CFLAGS  = -O3 -fopenmp -Wall -Wextra
TARGET  = matmul_hibrido
SRC     = matmul_hibrido.c

$(TARGET): $(SRC)
	$(CC) $(CFLAGS) $(SRC) -o $(TARGET)

verificar: $(TARGET)
	@echo "N,procesos,hilos,t_total,t_computo,gflops,verif"
	@OMP_NUM_THREADS=2 mpirun -np 4 ./$(TARGET) 240 2 1

clean:
	rm -f $(TARGET) resultados.csv

.PHONY: verificar clean
