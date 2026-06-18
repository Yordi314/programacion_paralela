# Suma paralela de un arreglo con OpenMP

Implementación en C de la suma de un arreglo de enteros usando **OpenMP**, con
medición de tiempos y análisis de **speedup**, **eficiencia**, **escalabilidad**
y **Ley de Amdahl**. Actividad de la asignatura *Computación Paralela y
Distribuida* (UNIBE).

## Archivos

| Archivo | Descripción |
|---|---|
| `suma_paralela.c` | Programa principal (suma con `reduction` de OpenMP) |
| `benchmark.sh` | Ejecuta el programa con 1, 2, 4, 8 y 16 hilos -> `resultados.csv` y genera el informe |
| `generar_informe.py` | Calcula métricas, ajusta Amdahl, dibuja las gráficas y construye el PDF |

## Requisitos

- GCC con soporte OpenMP (incluido por defecto).
- Python 3 con `numpy`, `scipy`, `matplotlib`, `reportlab`:

```bash
pip install numpy scipy matplotlib reportlab
```

## Compilar y ejecutar (un solo paso)

```bash
chmod +x benchmark.sh
./benchmark.sh                 # arreglo de 100 millones de enteros
# o, para otro tamaño:
./benchmark.sh 200000000
```

Esto compila el programa, lo ejecuta con 1, 2, 4, 8 y 16 hilos, guarda los
tiempos en `resultados.csv` y genera el informe `Informe_Suma_Paralela.pdf` con
**tus datos reales** (la tabla, las gráficas y el ajuste de Amdahl se calculan
solos).

## Ejecución manual

```bash
gcc -O2 -fopenmp suma_paralela.c -o suma_paralela
# Sintaxis: ./suma_paralela <N> <hilos> [repeticiones]
OMP_NUM_THREADS=4 ./suma_paralela 100000000 4 5
# Salida CSV: hilos,tiempo_s,suma
```

> El campo `suma` debe ser idéntico para cualquier número de hilos: es la
> verificación de correctitud.

## Directiva clave

```c
#pragma omp parallel for reduction(+:suma) schedule(static)
for (long long i = 0; i < N; ++i)
    suma += a[i];
```

`reduction(+:suma)` da a cada hilo una copia privada del acumulador y combina
las sumas parciales de forma segura al final, evitando la condición de carrera
sin serializar el acceso.
