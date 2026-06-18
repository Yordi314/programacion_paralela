#!/usr/bin/env bash
# =============================================================================
#  benchmark.sh - Mide el rendimiento del programa hibrido variando el numero
#  de procesos MPI y de hilos OpenMP, y guarda los resultados en CSV.
#
#  Uso:
#      ./benchmark.sh                 # usa valores por defecto
#      ./benchmark.sh 1200 3          # N=1200, 3 repeticiones por config
#
#  Importante: N debe ser divisible entre cada numero de procesos usado.
#  1200 es divisible entre 1,2,3,4,5,6 -> buena eleccion por defecto.
#
#  El baseline para el speedup es la corrida (1 proceso, 1 hilo).
# =============================================================================
set -euo pipefail

N=${1:-1200}                 # tamano de la matriz NxN
REPES=${2:-3}                # repeticiones por configuracion (se toma la mejor)
BIN=./matmul_hibrido
OUT=resultados.csv

PROCESOS=(1 2 4)             # ajusta segun nucleos/nodos disponibles
HILOS=(1 2 4)

# Compila si hace falta
[ -x "$BIN" ] || make

echo "N,procesos,hilos,t_total,t_computo,gflops,verif" > "$OUT"

for p in "${PROCESOS[@]}"; do
  if (( N % p != 0 )); then
    echo "Aviso: N=$N no es divisible entre $p procesos. Se omite." >&2
    continue
  fi
  for t in "${HILOS[@]}"; do
    mejor=""
    for r in $(seq 1 "$REPES"); do
      linea=$(OMP_NUM_THREADS="$t" mpirun -np "$p" "$BIN" "$N" "$t" 0)
      # Toma la corrida con menor t_total (campo 4)
      if [ -z "$mejor" ]; then
        mejor="$linea"
      else
        tm=$(echo "$mejor" | cut -d, -f4)
        tn=$(echo "$linea" | cut -d, -f4)
        awk "BEGIN{exit !($tn < $tm)}" && mejor="$linea"
      fi
    done
    echo "$mejor" | tee -a "$OUT"
  done
done

echo ""
echo "Listo. Resultados en $OUT"
echo "Ahora ejecuta:  python3 analizar_resultados.py $OUT"
