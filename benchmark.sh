#!/usr/bin/env bash
# =============================================================================
#  benchmark.sh - Ejecuta suma_paralela con 1, 2, 4, 8 y 16 hilos y guarda los
#  tiempos en resultados.csv. Luego genera el informe con tus datos reales.
#
#  Uso:
#      ./benchmark.sh                # N=100000000
#      ./benchmark.sh 200000000      # otro tamano de arreglo
# =============================================================================
set -euo pipefail

N=${1:-100000000}        # tamano del arreglo
REPES=5                   # repeticiones por configuracion (se toma la mejor)
BIN=./suma_paralela
OUT=resultados.csv
HILOS=(1 2 4 8 16)

[ -x "$BIN" ] || gcc -O2 -fopenmp suma_paralela.c -o "$BIN"

echo "hilos,tiempo,suma" > "$OUT"
for t in "${HILOS[@]}"; do
  echo "  ejecutando con $t hilo(s)..." >&2
  "$BIN" "$N" "$t" "$REPES" >> "$OUT"
done

echo "" >&2
echo "Tiempos guardados en $OUT" >&2
echo "Generando informe con tus datos reales..." >&2
python3 generar_informe.py
