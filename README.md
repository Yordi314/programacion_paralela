# Multiplicación de matrices — Aplicación híbrida MPI + OpenMP

Cálculo de `C = A × B` combinando **MPI** (distribución de tareas entre procesos)
y **OpenMP** (paralelización con hilos dentro de cada proceso).

## Archivos

| Archivo | Descripción |
|---|---|
| `matmul_hibrido.c` | Código fuente documentado |
| `Makefile` | Compilación y prueba de correctitud |
| `benchmark.sh` | Mide tiempos variando procesos e hilos → `resultados.csv` |
| `analizar_resultados.py` | Calcula speedup y eficiencia a partir del CSV |

## Requisitos

- Un compilador MPI (`mpicc`): **MPICH** u **OpenMPI**.
- Soporte OpenMP (incluido en GCC).

```bash
# Debian/Ubuntu
sudo apt-get install mpich            # o:  sudo apt-get install openmpi-bin libopenmpi-dev
```

## Compilar

```bash
make
```

## Verificar correctitud

Compara el resultado paralelo contra la multiplicación secuencial:

```bash
make verificar
# Esperado: ...,1  (el ultimo campo "verif"=1 significa resultado correcto)
```

## Ejecutar manualmente

```bash
# Sintaxis: ./matmul_hibrido <N> [hilos] [verificar(0|1)]
OMP_NUM_THREADS=4 mpirun -np 4 ./matmul_hibrido 1200 4 0
```

> **Restricción:** `N` debe ser divisible entre el número de procesos
> (`MPI_Scatter` reparte bloques de filas idénticos).

## Medir rendimiento

```bash
chmod +x benchmark.sh
./benchmark.sh 1200 3        # N=1200, 3 repeticiones por configuración
python3 analizar_resultados.py resultados.csv
```

Edita los arreglos `PROCESOS` e `HILOS` dentro de `benchmark.sh` según los
núcleos/nodos de tu máquina.

## Ejecución en clúster (varios nodos)

```bash
mpirun -np 8 -hostfile hosts.txt ./matmul_hibrido 4096 4 0
```

Donde `hosts.txt` lista los nodos (uno por línea, con `slots=` según núcleos).

## Diseño en breve

1. **Init** — `MPI_Init`, `MPI_Comm_rank`, `MPI_Comm_size`.
2. **Distribución** — `MPI_Bcast` envía `B` completa a todos; `MPI_Scatter`
   reparte bloques de filas de `A`.
3. **Cómputo** — cada proceso multiplica su bloque con
   `#pragma omp parallel for` (orden i-k-j por localidad de caché).
4. **Recolección** — `MPI_Gather` reúne los bloques de `C` en el proceso raíz.
5. **Sincronización** — los hilos escriben en filas **disjuntas** de la salida,
   así que **no hay condiciones de carrera**; `MPI_Barrier` delimita la
   medición de tiempo.
6. **Rendimiento** — `MPI_Wtime` mide tiempo total y de cómputo; el script
   calcula `speedup = T(1,1)/T(p,h)` y `eficiencia = speedup/(p·h)`.
