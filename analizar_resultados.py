#!/usr/bin/env python3
# =============================================================================
#  analizar_resultados.py - Calcula speedup y eficiencia a partir del CSV
#  producido por benchmark.sh, e imprime una tabla lista para el informe.
#
#      speedup(p,h)    = T(1,1) / T(p,h)
#      eficiencia(p,h) = speedup / (p * h)
#
#  Uso:  python3 analizar_resultados.py resultados.csv
# =============================================================================
import csv
import sys

ruta = sys.argv[1] if len(sys.argv) > 1 else "resultados.csv"

filas = []
with open(ruta, newline="") as f:
    for fila in csv.DictReader(f):
        filas.append({
            "procesos": int(fila["procesos"]),
            "hilos":    int(fila["hilos"]),
            "t_total":  float(fila["t_total"]),
            "t_comp":   float(fila["t_computo"]),
            "gflops":   float(fila["gflops"]),
        })

if not filas:
    sys.exit("CSV vacio o no encontrado: " + ruta)

# Baseline: 1 proceso, 1 hilo (la configuracion secuencial)
base = next((r for r in filas if r["procesos"] == 1 and r["hilos"] == 1), None)
if base is None:
    sys.exit("Falta la corrida baseline (1 proceso, 1 hilo) en el CSV.")
T1 = base["t_total"]

print(f"\nBaseline secuencial T(1,1) = {T1:.4f} s\n")
print(f"{'Procesos':>8} {'Hilos':>6} {'Unid.':>6} {'T_total(s)':>11} "
      f"{'Speedup':>8} {'Eficiencia':>11} {'GFLOP/s':>9}")
print("-" * 64)

for r in sorted(filas, key=lambda x: (x["procesos"], x["hilos"])):
    unidades = r["procesos"] * r["hilos"]
    speedup  = T1 / r["t_total"]
    eficien  = speedup / unidades
    print(f"{r['procesos']:>8} {r['hilos']:>6} {unidades:>6} "
          f"{r['t_total']:>11.4f} {speedup:>8.2f} {eficien:>11.2%} "
          f"{r['gflops']:>9.2f}")

print("\nNota: 'Unid.' = procesos x hilos (unidades de computo totales).")
print("Eficiencia cercana a 100% indica escalado casi ideal.\n")
