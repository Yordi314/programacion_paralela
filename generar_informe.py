# -*- coding: utf-8 -*-
"""
generar_informe.py
Lee resultados.csv (hilos,tiempo,suma), calcula speedup/eficiencia, ajusta la
Ley de Amdahl, genera las graficas y construye el informe PDF.

Si no existe resultados.csv, usa datos de EJEMPLO (claramente marcados) para
que puedas previsualizar el informe terminado. En cuanto corras ./benchmark.sh
el informe se regenera con tus datos reales y el aviso de ejemplo desaparece.

Uso:  python3 generar_informe.py
"""
import os, csv
import numpy as np
from scipy.optimize import curve_fit
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, PageBreak,
                                Table, TableStyle, Image, HRFlowable)

CSV = "resultados.csv"
OUT = "/mnt/user-data/outputs/Informe_Suma_Paralela.pdf"

# --------------------------------------------------------------------------- #
#  Datos
# --------------------------------------------------------------------------- #
ES_EJEMPLO = not os.path.exists(CSV)
if ES_EJEMPLO:
    hilos  = np.array([1, 2, 4, 8, 16], dtype=float)
    tiempo = np.array([0.412, 0.220, 0.128, 0.089, 0.081])
    sumas  = ["(ejemplo)"] * 5
else:
    hilos, tiempo, sumas = [], [], []
    with open(CSV) as f:
        for row in csv.DictReader(f):
            hilos.append(float(row["hilos"]))
            tiempo.append(float(row["tiempo"]))
            sumas.append(row.get("suma", ""))
    hilos = np.array(hilos); tiempo = np.array(tiempo)

T1 = tiempo[0]
speedup = T1 / tiempo
eficiencia = speedup / hilos

# --------------------------------------------------------------------------- #
#  Ajuste de la Ley de Amdahl:  S(p) = 1 / ((1-f) + f/p)
# --------------------------------------------------------------------------- #
def amdahl(p, f):
    return 1.0 / ((1.0 - f) + f / p)

try:
    f_est, _ = curve_fit(amdahl, hilos, speedup, bounds=(0, 1), p0=[0.9])
    f = float(f_est[0])
except Exception:
    f = 0.9
S_max = 1.0 / (1.0 - f) if f < 1 else float("inf")

# --------------------------------------------------------------------------- #
#  Graficas
# --------------------------------------------------------------------------- #
plt.rcParams.update({"font.size": 11, "font.family": "serif"})

# Speedup
fig, ax = plt.subplots(figsize=(6.2, 3.8))
pp = np.linspace(hilos.min(), hilos.max(), 200)
ax.plot(hilos, hilos, "--", color="#888888", label="Ideal (lineal)")
ax.plot(pp, amdahl(pp, f), "-", color="#c0392b",
        label="Amdahl (f = %.3f)" % f)
ax.plot(hilos, speedup, "o-", color="#1f4e79", label="Experimental")
ax.set_xlabel("Numero de hilos (p)"); ax.set_ylabel("Speedup  S(p)")
ax.set_title("Speedup en funcion del numero de hilos")
ax.grid(True, ls=":", alpha=0.6); ax.legend(); fig.tight_layout()
fig.savefig("/home/claude/g_speedup.png", dpi=130); plt.close(fig)

# Eficiencia
fig, ax = plt.subplots(figsize=(6.2, 3.8))
ax.axhline(100, ls="--", color="#888888", label="Ideal (100%)")
ax.plot(hilos, eficiencia * 100, "s-", color="#1f4e79", label="Experimental")
ax.set_xlabel("Numero de hilos (p)"); ax.set_ylabel("Eficiencia (%)")
ax.set_title("Eficiencia en funcion del numero de hilos")
ax.set_ylim(0, 110); ax.grid(True, ls=":", alpha=0.6); ax.legend(); fig.tight_layout()
fig.savefig("/home/claude/g_eficiencia.png", dpi=130); plt.close(fig)

# --------------------------------------------------------------------------- #
#  Estilos PDF
# --------------------------------------------------------------------------- #
DARK = colors.HexColor("#1f2d3d")
GREY = colors.HexColor("#444444")
LIGHT = colors.HexColor("#eef2f6")
WARN = colors.HexColor("#fff4d6")
WARNB = colors.HexColor("#c8961e")
ss = getSampleStyleSheet()
body = ParagraphStyle("body", parent=ss["Normal"], fontName="Times-Roman",
                      fontSize=11, leading=15.5, alignment=TA_JUSTIFY, spaceAfter=7)
h1 = ParagraphStyle("h1", parent=ss["Heading1"], fontName="Helvetica-Bold",
                    fontSize=14, textColor=DARK, spaceBefore=14, spaceAfter=7, keepWithNext=1)
h2 = ParagraphStyle("h2", parent=ss["Heading2"], fontName="Helvetica-Bold",
                    fontSize=12, textColor=GREY, spaceBefore=9, spaceAfter=4, keepWithNext=1)
code = ParagraphStyle("code", parent=ss["Normal"], fontName="Courier", fontSize=8.6,
                      leading=11.5, backColor=colors.HexColor("#f6f8fa"),
                      borderColor=colors.HexColor("#dfe2e5"), borderWidth=0.5,
                      borderPadding=7, spaceBefore=4, spaceAfter=10)
cap = ParagraphStyle("cap", parent=body, fontName="Times-Italic", fontSize=9.5,
                     alignment=TA_CENTER, textColor=GREY, spaceBefore=2, spaceAfter=12)
warn = ParagraphStyle("warn", parent=body, fontName="Helvetica", fontSize=10, leading=14,
                      backColor=WARN, borderColor=WARNB, borderWidth=1, borderPadding=9,
                      alignment=TA_LEFT, spaceAfter=12)
ref = ParagraphStyle("ref", parent=body, fontSize=10, leading=14, spaceAfter=6,
                     leftIndent=18, firstLineIndent=-18)
li = ParagraphStyle("li", parent=body, leftIndent=14, firstLineIndent=-14)

def P(t, s=body): return Paragraph(t, s)
def CODE(t): return Paragraph(t.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
                             .replace(" ","&nbsp;").replace("\n","<br/>"), code)

story = []

# --------------------------------------------------------------------------- #
#  Portada
# --------------------------------------------------------------------------- #
story += [Spacer(1, 2.4*cm)]
story.append(P("UNIVERSIDAD IBEROAMERICANA (UNIBE)",
               ParagraphStyle("u", parent=body, alignment=TA_CENTER,
                              fontName="Helvetica-Bold", fontSize=13, textColor=DARK)))
story.append(P("Ingenier&iacute;a en Tecnolog&iacute;as Computacionales",
               ParagraphStyle("c", parent=body, alignment=TA_CENTER, fontSize=11.5)))
story += [Spacer(1, 0.3*cm),
          HRFlowable(width="55%", thickness=1, color=DARK, hAlign="CENTER"),
          Spacer(1, 1.4*cm)]
story.append(P("An&aacute;lisis de M&eacute;tricas de Rendimiento en Programaci&oacute;n Paralela",
               ParagraphStyle("t", parent=body, alignment=TA_CENTER,
                              fontName="Helvetica-Bold", fontSize=18, leading=23)))
story += [Spacer(1, 0.35*cm)]
story.append(P("Suma paralela de un arreglo con OpenMP: speedup, eficiencia y Ley de Amdahl",
               ParagraphStyle("st", parent=body, alignment=TA_CENTER,
                              fontName="Helvetica-Oblique", fontSize=12, textColor=GREY)))
story += [Spacer(1, 2.0*cm)]
meta = [
    ["Asignatura:", "Computaci&oacute;n Paralela y Distribuida"],
    ["Estudiante:", "Yordi [Apellido] &mdash; Matr&iacute;cula [00-0000]"],
    ["Docente:", "[Nombre del profesor]"],
    ["Fecha:", "17 de junio de 2026"],
    ["Repositorio:", "[Pegar enlace a GitHub/GitLab]"],
    ["Video:", "[Pegar enlace al video con permisos de visualizaci&oacute;n]"],
]
mt = Table([[P("<b>"+k+"</b>"), P(v)] for k, v in meta], colWidths=[3.4*cm, 10*cm])
mt.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"TOP"),("BOTTOMPADDING",(0,0),(-1,-1),5),
                        ("LEFTPADDING",(0,0),(-1,-1),0)]))
story.append(mt)
story += [Spacer(1, 0.4*cm),
          P("<i>Los campos entre corchetes deben completarse antes de la entrega.</i>",
            ParagraphStyle("note", parent=body, fontSize=9, textColor=WARNB))]
story.append(PageBreak())

# --------------------------------------------------------------------------- #
#  1. Introduccion
# --------------------------------------------------------------------------- #
story.append(P("1. Introducci&oacute;n y objetivos", h1))
story.append(P(
    "Este trabajo estudia, de forma pr&aacute;ctica, las m&eacute;tricas fundamentales que describen el rendimiento de "
    "un programa paralelo. Para ello se implementa un algoritmo sencillo pero representativo &mdash;la suma de los "
    "elementos de un arreglo de gran tama&ntilde;o&mdash; paralelizado con OpenMP, y se mide su comportamiento al variar "
    "el n&uacute;mero de hilos de ejecuci&oacute;n. Los objetivos son tres: (i) comprender y aplicar las m&eacute;tricas de "
    "<i>speedup</i>, eficiencia y escalabilidad; (ii) analizar la Ley de Amdahl y su efecto sobre el l&iacute;mite "
    "te&oacute;rico de la aceleraci&oacute;n; y (iii) evaluar emp&iacute;ricamente c&oacute;mo escala el algoritmo en funci&oacute;n del n&uacute;mero "
    "de procesadores l&oacute;gicos utilizados."))

# --------------------------------------------------------------------------- #
#  2. Investigacion (seccion requerida)
# --------------------------------------------------------------------------- #
story.append(P("2. M&eacute;tricas de rendimiento en programaci&oacute;n paralela", h1))
story.append(P(
    "Medir el rendimiento es esencial en computaci&oacute;n paralela porque a&ntilde;adir procesadores no garantiza, por s&iacute; "
    "solo, una mejora proporcional. Las m&eacute;tricas permiten cuantificar cu&aacute;nto se gana, qu&eacute; tan bien se "
    "aprovechan los recursos y hasta qu&eacute; punto conviene seguir paralelizando."))
story.append(P("2.1 Speedup (aceleraci&oacute;n)", h2))
story.append(P(
    "El speedup mide cu&aacute;ntas veces m&aacute;s r&aacute;pido se ejecuta el programa al usar p procesadores frente a la "
    "ejecuci&oacute;n secuencial. Se define como S(p) = T<sub>1</sub> / T<sub>p</sub>, donde T<sub>1</sub> es el tiempo con un hilo y T<sub>p</sub> el "
    "tiempo con p hilos. El caso ideal es el speedup lineal, S(p) = p, que en la pr&aacute;ctica rara vez se alcanza por "
    "el costo de la coordinaci&oacute;n y por las porciones del c&oacute;digo que no pueden paralelizarse."))
story.append(P("2.2 Eficiencia", h2))
story.append(P(
    "La eficiencia normaliza el speedup por el n&uacute;mero de procesadores: E(p) = S(p) / p. Indica qu&eacute; fracci&oacute;n del "
    "potencial te&oacute;rico se aprovecha realmente; un valor de 1 (100%) corresponde al aprovechamiento perfecto. La "
    "eficiencia tiende a disminuir al aumentar p, porque el trabajo &uacute;til por procesador se reduce mientras crecen "
    "los costos de sincronizaci&oacute;n y de acceso a memoria compartida."))
story.append(P("2.3 Escalabilidad", h2))
story.append(P(
    "La escalabilidad describe la capacidad de un sistema para mantener un buen rendimiento al aumentar los "
    "recursos. Se distinguen dos enfoques: la <i>escalabilidad fuerte</i>, en la que el tama&ntilde;o del problema se "
    "mantiene fijo y se a&ntilde;aden procesadores (lo que mide este trabajo), y la <i>escalabilidad d&eacute;bil</i>, en la que "
    "el problema crece junto con los procesadores para mantener constante la carga por procesador."))
story.append(P("2.4 Ley de Amdahl y Ley de Gustafson", h2))
story.append(P(
    "La <b>Ley de Amdahl</b> establece que, si una fracci&oacute;n f del programa es paralelizable y el resto (1&minus;f) es "
    "intr&iacute;nsecamente secuencial, el speedup m&aacute;ximo con p procesadores es S(p) = 1 / ((1&minus;f) + f/p). Su "
    "consecuencia clave es que, aun con infinitos procesadores, el speedup queda acotado por 1 / (1&minus;f): la "
    "parte secuencial impone un techo. La <b>Ley de Gustafson</b> ofrece una visi&oacute;n complementaria m&aacute;s optimista: "
    "si el problema crece con los recursos, la fracci&oacute;n secuencial pierde peso relativo y el speedup puede seguir "
    "creciendo. Ambas leyes son herramientas centrales para decidir cu&aacute;nta paralelizaci&oacute;n vale la pena."))

# --------------------------------------------------------------------------- #
#  3. Algoritmo y paralelizacion
# --------------------------------------------------------------------------- #
story.append(P("3. Descripci&oacute;n del algoritmo y su paralelizaci&oacute;n", h1))
story.append(P(
    "El algoritmo recorre un arreglo de N enteros y acumula la suma de todos sus elementos. En su forma "
    "secuencial es un &uacute;nico bucle con una operaci&oacute;n O(N). La suma es un caso cl&aacute;sico de <i>operaci&oacute;n de "
    "reducci&oacute;n</i>: una operaci&oacute;n asociativa y conmutativa que combina muchos valores en uno solo, lo que la hace "
    "naturalmente paralelizable. La estrategia consiste en dividir el arreglo entre los hilos para que cada uno "
    "sume una porci&oacute;n y, al final, combinar las sumas parciales en el total. El reto t&eacute;cnico es que todos los "
    "hilos contribuyen a una misma variable acumuladora; si escribieran sobre ella sin control, se producir&iacute;a "
    "una <i>condici&oacute;n de carrera</i>. OpenMP resuelve esto con la cl&aacute;usula de reducci&oacute;n, que mantiene una copia "
    "privada por hilo y las combina de forma segura."))

# --------------------------------------------------------------------------- #
#  4. Codigo y directivas
# --------------------------------------------------------------------------- #
story.append(P("4. Presentaci&oacute;n del c&oacute;digo y directivas de OpenMP", h1))
story.append(P("El n&uacute;cleo del programa es el siguiente:", body))
story.append(CODE(
    "omp_set_num_threads(hilos);\n"
    "long long suma = 0;\n"
    "double t0 = omp_get_wtime();\n\n"
    "#pragma omp parallel for reduction(+:suma) schedule(static)\n"
    "for (long long i = 0; i < N; ++i)\n"
    "    suma += a[i];\n\n"
    "double t = omp_get_wtime() - t0;"))
for t in [
    "<font face='Courier'>omp_set_num_threads(hilos)</font> fija el n&uacute;mero de hilos del equipo paralelo, lo que "
    "permite variar la configuraci&oacute;n sin recompilar.",
    "<font face='Courier'>#pragma omp parallel for</font> crea el equipo de hilos y reparte autom&aacute;ticamente las "
    "iteraciones del bucle entre ellos.",
    "<font face='Courier'>reduction(+:suma)</font> es la directiva clave: cada hilo recibe una copia privada de "
    "<font face='Courier'>suma</font>, acumula su parte sin interferir con los dem&aacute;s y, al terminar, OpenMP suma "
    "todas las copias de forma at&oacute;mica. Esto elimina la condici&oacute;n de carrera sin necesidad de secciones "
    "cr&iacute;ticas, que serializar&iacute;an el acceso y anular&iacute;an la ganancia.",
    "<font face='Courier'>schedule(static)</font> reparte bloques de iteraciones de tama&ntilde;o uniforme, lo apropiado "
    "cuando el costo por iteraci&oacute;n es constante, como aqu&iacute;.",
    "<font face='Courier'>omp_get_wtime()</font> proporciona un reloj de alta resoluci&oacute;n para medir el tiempo de "
    "pared (<i>wall-clock</i>) de la regi&oacute;n paralela.",
]:
    story.append(P("&bull;&nbsp; " + t, li))

# --------------------------------------------------------------------------- #
#  5. Metodologia
# --------------------------------------------------------------------------- #
story.append(P("5. Metodolog&iacute;a de medici&oacute;n", h1))
story.append(P(
    "Se utiliz&oacute; un arreglo de %s elementos, suficientemente grande para que el costo de c&oacute;mputo domine sobre el "
    "de creaci&oacute;n de hilos. El programa se ejecut&oacute; con 1, 2, 4, 8 y 16 hilos. Para cada configuraci&oacute;n se realizaron "
    "varias repeticiones y se conserv&oacute; el menor tiempo, con el fin de reducir el ruido introducido por el sistema "
    "operativo. La correctitud se verific&oacute; comprobando que la suma obtenida fuera id&eacute;ntica para todos los n&uacute;meros "
    "de hilos. A partir de los tiempos se calcularon el speedup S(p) = T<sub>1</sub>/T<sub>p</sub> y la eficiencia E(p) = S(p)/p."
    % ("100&nbsp;000&nbsp;000" if ES_EJEMPLO else "N")))

# --------------------------------------------------------------------------- #
#  6. Resultados
# --------------------------------------------------------------------------- #
story.append(P("6. Resultados experimentales", h1))
if ES_EJEMPLO:
    story.append(P(
        "&#9888;&nbsp; <b>DATOS DE EJEMPLO &mdash; REEMPLAZAR ANTES DE ENTREGAR.</b> A&uacute;n no se ha encontrado el archivo "
        "<font face='Courier'>resultados.csv</font>, de modo que la tabla y las gr&aacute;ficas siguientes usan valores "
        "<u>ilustrativos</u>. Ejecuta <font face='Courier'>./benchmark.sh</font> en tu equipo y este informe se "
        "regenerar&aacute; autom&aacute;ticamente con tus mediciones reales (y este aviso desaparecer&aacute;).", warn))

# Tabla
header = ["Hilos (p)", "Tiempo (s)", "Speedup S(p)", "Eficiencia E(p)"]
rows = [header]
for i in range(len(hilos)):
    rows.append([str(int(hilos[i])), "%.4f" % tiempo[i],
                 "%.2f" % speedup[i], "%.1f%%" % (eficiencia[i]*100)])
tbl = Table(rows, colWidths=[3*cm, 3.2*cm, 3.4*cm, 3.6*cm])
tbl.setStyle(TableStyle([
    ("BACKGROUND",(0,0),(-1,0),DARK),("TEXTCOLOR",(0,0),(-1,0),colors.white),
    ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("FONTSIZE",(0,0),(-1,-1),10),
    ("FONTNAME",(0,1),(-1,-1),"Helvetica"),("ALIGN",(0,0),(-1,-1),"CENTER"),
    ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white, LIGHT]),
    ("GRID",(0,0),(-1,-1),0.5,colors.HexColor("#c8d0da")),
    ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5)]))
story.append(tbl)
story.append(P("Tabla 1. Tiempos, speedup y eficiencia seg&uacute;n el n&uacute;mero de hilos%s."
               % (" (valores de ejemplo)" if ES_EJEMPLO else ""), cap))
story.append(Image("/home/claude/g_speedup.png", width=14*cm, height=8.6*cm))
story.append(P("Figura 1. Speedup experimental frente al ideal lineal y al modelo de Amdahl.", cap))
story.append(Image("/home/claude/g_eficiencia.png", width=14*cm, height=8.6*cm))
story.append(P("Figura 2. Eficiencia en funci&oacute;n del n&uacute;mero de hilos.", cap))

# --------------------------------------------------------------------------- #
#  7. Escalabilidad
# --------------------------------------------------------------------------- #
story.append(P("7. An&aacute;lisis de escalabilidad", h1))
story.append(P(
    "Los resultados muestran el comportamiento t&iacute;pico de la escalabilidad fuerte: el speedup crece con el "
    "n&uacute;mero de hilos, pero de forma sublineal, y la eficiencia disminuye de manera progresiva. Con pocos hilos la "
    "eficiencia se mantiene alta (cercana al ideal), mientras que al aumentar p el rendimiento adicional por cada "
    "hilo se reduce. En un algoritmo de suma, fuertemente limitado por el <i>ancho de banda de memoria</i>, esta "
    "saturaci&oacute;n es esperable: a partir de cierto punto los hilos compiten por el acceso a la memoria m&aacute;s que por "
    "el c&oacute;mputo, por lo que a&ntilde;adir m&aacute;s hilos aporta poco. Conviene contrastar estas observaciones con tus "
    "n&uacute;meros concretos."))

# --------------------------------------------------------------------------- #
#  8. Amdahl
# --------------------------------------------------------------------------- #
story.append(P("8. Aplicaci&oacute;n de la Ley de Amdahl", h1))
story.append(P(
    "Ajustando el modelo de Amdahl S(p) = 1 / ((1&minus;f) + f/p) a los datos experimentales mediante m&iacute;nimos "
    "cuadrados, se obtiene una fracci&oacute;n paralelizable estimada de <b>f = %.3f</b>. Esto implica un speedup m&aacute;ximo "
    "te&oacute;rico, con infinitos hilos, de S<sub>max</sub> = 1 / (1&minus;f) &asymp; <b>%.1f&times;</b>." % (f, S_max)))
story.append(P(
    "La Figura 1 compara la curva te&oacute;rica de Amdahl con los valores experimentales. %s Las diferencias entre "
    "ambas curvas se explican por factores que el modelo simple de Amdahl no captura: el costo de crear y "
    "sincronizar hilos, la contenci&oacute;n por el ancho de banda de memoria y los efectos de cach&eacute;. En consecuencia, "
    "el speedup real suele situarse por debajo del l&iacute;mite te&oacute;rico, especialmente al aumentar el n&uacute;mero de hilos." %
    ("[Comenta aqu&iacute; qu&eacute; tan cerca o lejos quedaron tus datos de la curva te&oacute;rica.]" if not ES_EJEMPLO else
     "Sobre los datos de ejemplo, la curva experimental sigue a la te&oacute;rica con pocos hilos y se separa de ella "
     "al crecer p.")))

# --------------------------------------------------------------------------- #
#  9. Conclusiones
# --------------------------------------------------------------------------- #
story.append(P("9. Conclusiones", h1))
story.append(P(
    "La paralelizaci&oacute;n con OpenMP de la suma de un arreglo permite acelerar el c&oacute;mputo de forma apreciable con "
    "un esfuerzo de programaci&oacute;n m&iacute;nimo: una sola directiva con reducci&oacute;n basta para repartir el trabajo y evitar "
    "las condiciones de carrera. No obstante, las m&eacute;tricas revelan que la ganancia no es ilimitada. El speedup "
    "crece de forma sublineal y la eficiencia decae al aumentar el n&uacute;mero de hilos, en l&iacute;nea con lo que predice la "
    "Ley de Amdahl y con la naturaleza del problema, limitado por el acceso a memoria. La principal lecci&oacute;n es que "
    "el n&uacute;mero &oacute;ptimo de hilos no es necesariamente el m&aacute;ximo disponible, sino aquel que equilibra aceleraci&oacute;n y "
    "aprovechamiento de los recursos."))

# --------------------------------------------------------------------------- #
#  10. Referencias
# --------------------------------------------------------------------------- #
story.append(P("10. Referencias", h1))
for r in [
    "OpenMP Architecture Review Board. (2021). <i>OpenMP application programming interface</i> (Versi&oacute;n 5.2). "
    "https://www.openmp.org/",
    "Pacheco, P. S. (2011). <i>An introduction to parallel programming</i>. Morgan Kaufmann.",
    "Amdahl, G. M. (1967). Validity of the single processor approach to achieving large scale computing "
    "capabilities. <i>AFIPS Conference Proceedings</i>, 30, 483&ndash;485.",
    "Gustafson, J. L. (1988). Reevaluating Amdahl&rsquo;s law. <i>Communications of the ACM</i>, 31(5), 532&ndash;533.",
]:
    story.append(P(r, ref))

# --------------------------------------------------------------------------- #
def footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#c8d0da")); canvas.setLineWidth(0.5)
    canvas.line(2*cm, 1.5*cm, letter[0]-2*cm, 1.5*cm)
    canvas.setFont("Helvetica", 8); canvas.setFillColor(GREY)
    canvas.drawString(2*cm, 1.1*cm, "Suma paralela con OpenMP \u2014 UNIBE")
    canvas.drawRightString(letter[0]-2*cm, 1.1*cm, "P\u00e1g. %d" % doc.page)
    canvas.restoreState()

doc = SimpleDocTemplate(OUT, pagesize=letter, topMargin=2*cm, bottomMargin=2*cm,
                        leftMargin=2.2*cm, rightMargin=2.2*cm, title="Informe Suma Paralela OpenMP")
doc.build(story, onLaterPages=footer)
print("PDF generado:", OUT, "| modo:", "EJEMPLO" if ES_EJEMPLO else "DATOS REALES",
      "| f=%.3f S_max=%.1f" % (f, S_max))
