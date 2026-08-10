"""Sector 2 of the 30-year CAGR series: AI compute and infrastructure.

Unlike sector 1 this one is built around the valuation question: where the
$725bn of 2026 hyperscaler capex actually lands, which multiples are cheap
against which margins, and what the cost of that capital is.

All market figures are sourced from public data pulled in August 2026 and are
labelled as such in the document; sources differ on several of them and the
report shows the ranges rather than picking one.
"""

import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from reportlab.lib.units import cm

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.visualization.sector_report import (  # noqa: E402
    bullets, build, chart, cover, h1, h2, key_box, p, table, tier_table,
    warn_box,
)
from reportlab.platypus import PageBreak, Spacer  # noqa: E402

OUT = os.path.join(os.path.dirname(__file__), "..", "computo_ia_valoracion.pdf")
TMP = os.environ.get("SCRATCH", "/tmp")

PLOT_INK = "#141821"
PLOT_ACCENT = "#1F6F8B"
PLOT_MUTED = "#8C97A3"
PLOT_WARN = "#C8792B"


def _style_axes(ax):
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color("#C9D2DB")
    ax.tick_params(colors="#5A6472", labelsize=8)
    ax.set_axisbelow(True)


# --------------------------------------------------------------------------
# Chart 1 — the quality/price plane: what you pay against what it earns
# --------------------------------------------------------------------------

def chart_roic_vs_pe():
    # (name, ROIC %, forward P/E, label offset x, offset y)
    pts = [
        ("Nvidia",      104.7, 23.5,   0, 16),
        ("TSMC",         54.6, 22.0,   0, 16),
        ("ASML",         66.0, 39.2,   0, 16),
        ("Broadcom",     24.2, 22.0,   0, -22),
        ("Micron",       67.6,  5.8,   0, -22),
        ("SK Hynix",     51.8,  4.4,   0, 16),
        ("Synopsys",      2.3, 35.0,  18, 10),
        ("KLA",          40.0, 32.0,   0, 16),
        ("Lam Research", 30.0, 38.1,   0, -22),
        ("Tokyo Electron", 23.0, 28.0, 0, 16),
    ]
    fig, ax = plt.subplots(figsize=(9.2, 5.6), dpi=200)
    _style_axes(ax)

    for name, roic, pe, dx, dy in pts:
        cheapish = pe < 12
        col = PLOT_WARN if cheapish else PLOT_ACCENT
        ax.scatter(roic, pe, s=260, color=col, zorder=3,
                   edgecolor="white", linewidth=1.5)
        ax.annotate(name, (roic, pe), textcoords="offset points",
                    xytext=(dx, dy), ha="center", fontsize=7.8,
                    color=PLOT_INK)

    ax.axhline(12, color=PLOT_WARN, lw=0.9, ls="--", zorder=1)
    ax.annotate("zona de múltiplo bajo sobre beneficio de pico",
                (108, 8.6), fontsize=7, color=PLOT_WARN, ha="right")

    ax.set_xlabel("ROIC (%) — lo que el negocio gana sobre el capital empleado",
                  fontsize=8.5, color=PLOT_INK)
    ax.set_ylabel("PER adelantado (veces)", fontsize=8.5, color=PLOT_INK)
    ax.set_xlim(-5, 115)
    ax.set_ylim(0, 45)
    ax.grid(axis="both", color="#E4EAEF", lw=0.7)
    fig.tight_layout()
    path = os.path.join(TMP, "roic_pe.png")
    fig.savefig(path, facecolor="white")
    plt.close(fig)
    return path


# --------------------------------------------------------------------------
# Chart 2 — the gap the whole sector rests on
# --------------------------------------------------------------------------

def chart_capex_gap():
    fig, ax = plt.subplots(figsize=(9.2, 4.0), dpi=200)
    _style_axes(ax)

    labels = ["Capex hiperescaladores\n2025", "Capex hiperescaladores\n2026 (guía)",
              "Ingreso anualizado\nIA pura (Anthropic +\nOpenAI + resto)"]
    vals = [388, 725, 100]
    cols = [PLOT_ACCENT, PLOT_ACCENT, PLOT_WARN]
    bars = ax.bar(labels, vals, color=cols, width=0.55)
    for b, v in zip(bars, vals):
        ax.annotate(f"{v} mm$", (b.get_x() + b.get_width() / 2, v),
                    textcoords="offset points", xytext=(0, 5),
                    ha="center", fontsize=9, weight="bold", color=PLOT_INK)
    ax.set_ylabel("Miles de millones de dólares", fontsize=8.5, color=PLOT_INK)
    ax.set_ylim(0, 830)
    ax.grid(axis="y", color="#E4EAEF", lw=0.7)
    fig.tight_layout()
    path = os.path.join(TMP, "capexgap.png")
    fig.savefig(path, facecolor="white")
    plt.close(fig)
    return path


# --------------------------------------------------------------------------
# Chart 3 — the accounting lever nobody prices
# --------------------------------------------------------------------------

def chart_depreciation():
    lives = [6, 5, 4, 3]
    vintage = 725.0
    annual = [vintage / L for L in lives]

    fig, ax = plt.subplots(figsize=(9.2, 3.8), dpi=200)
    _style_axes(ax)
    labels = [f"{L} años" for L in lives]
    cols = [PLOT_ACCENT, "#3E8FA6", PLOT_WARN, "#A8452B"]
    bars = ax.barh(labels[::-1], annual[::-1], color=cols[::-1], height=0.55)
    for b, v in zip(bars, annual[::-1]):
        ax.annotate(f"{v:,.0f} mm$/año", (v, b.get_y() + b.get_height() / 2),
                    textcoords="offset points", xytext=(6, 0),
                    va="center", fontsize=8.5, weight="bold", color=PLOT_INK)
    ax.set_xlabel("Amortización anual generada por una sola añada de capex de 725 mm$",
                  fontsize=8.5, color=PLOT_INK)
    ax.set_xlim(0, 310)
    ax.grid(axis="x", color="#E4EAEF", lw=0.7)
    fig.tight_layout()
    path = os.path.join(TMP, "deprec.png")
    fig.savefig(path, facecolor="white")
    plt.close(fig)
    return path


# --------------------------------------------------------------------------
# Story
# --------------------------------------------------------------------------

def story():
    s = []
    s += cover(
        "Cómputo e<br/>infraestructura de IA",
        "Dónde acaba el dinero, qué múltiplo se paga por él<br/>"
        "y por qué lo más barato del sector es lo más peligroso",
        "SERIE CAGR 30 AÑOS &nbsp;&middot;&nbsp; SECTOR 2 DE 8",
        [("Horizonte", "2026 - 2056"),
         ("Enfoque", "Valoración, márgenes, retorno sobre capital y coste"),
         ("Datos de mercado", "Agosto 2026, fuentes públicas"),
         ("Fecha", "Agosto 2026")],
    )

    # -- 1 ------------------------------------------------------------------
    s.append(h1("El flujo de capital: quién paga y quién cobra", 1))
    s.append(p(
        "Este sector no se entiende mirando productos. Se entiende siguiendo un "
        "único río de dinero: los cuatro grandes hiperescaladores han guiado a "
        "unos <b>725.000 millones de dólares de inversión en 2026</b>, frente a "
        "unos 388.000 millones en 2025. Es un incremento del orden del 60% en un "
        "solo ejercicio, y es la variable de la que depende, directa o "
        "indirectamente, el beneficio de casi todas las compañías del informe.",
        "lead"))
    s.append(p(
        "Amazon guía en torno a 200.000 millones, Microsoft y Google entre "
        "110.000 y 185.000 según la fuente y el perímetro, y Meta entre 115.000 "
        "y 135.000 &mdash; esta última sin nube pública con la que monetizarlo "
        "directamente. La composición importa tanto como el total: una parte "
        "mayoritaria del gasto no va a chips, sino a obra civil, potencia "
        "eléctrica y refrigeración, que es precisamente el puente con el sector "
        "1 de esta serie."))
    s.append(chart(chart_capex_gap(), 16.0))
    s.append(p(
        "Cifras de guía de las compañías y estimaciones de mercado, agosto de "
        "2026. El ingreso de IA pura agrega los run-rate anualizados públicos de "
        "los principales proveedores de modelos.", "caption"))
    s.append(warn_box(
        "La comparación anterior es real, pero hay que leerla con honestidad",
        "El gráfico enfrenta el capex con el ingreso de las compañías de IA "
        "pura, y esa no es la comparación completa: los hiperescaladores "
        "monetizan la inversión también a través de sus propias nubes, de "
        "publicidad y de producto interno, y esos ingresos no aparecen en la "
        "barra naranja. Pero el orden de magnitud sigue en pie: se está "
        "invirtiendo del orden de siete veces lo que factura hoy toda la capa de "
        "modelos. La tesis alcista no es que esa brecha no exista, sino que se "
        "cierra con el tiempo. La bajista es que el capex es anual y recurrente "
        "mientras el cierre de la brecha es una promesa."))

    # -- 2 ------------------------------------------------------------------
    s.append(h1("El mapa real de márgenes, retornos y múltiplos", 2))
    s.append(p(
        "Aquí está el núcleo de lo que pediste. La tabla reúne, con datos "
        "públicos de agosto de 2026, lo que cada negocio gana, sobre cuánto "
        "capital lo gana, y lo que el mercado cobra por ello.", "lead"))
    s.append(table(
        ["Compañía", "PER adel.", "EV/EBITDA", "Margen bruto",
         "Margen oper.", "ROIC", "Lectura"],
        [
            ["Nvidia", "22-24x", "32,5x", "74,2%", "~60%", "104,7%",
             "El mejor negocio; el riesgo no es el múltiplo sino la sostenibilidad del beneficio"],
            ["TSMC", "19-25x", "18,6x", "67,7%", "60,3%", "54,6%",
             "<b>La mejor relación calidad-precio del sector</b>"],
            ["ASML", "39x", "43,5x", "53-56%", "36,0%", "66,0%",
             "Monopolio real al múltiplo más alto y con el margen operativo más bajo del grupo"],
            ["Broadcom", "22x", "49,0x*", "67,8%", "n.d.", "24,2%",
             "ROIC muy inferior al resto por el peso de las adquisiciones"],
            ["Micron", "5,6-6,1x", "14-15x", "72,6%", "n.d.", "67,6%",
             "Múltiplo mínimo sobre margen máximo: la señal clásica de pico de ciclo"],
            ["SK Hynix", "4,4x", "n.d.", "n.d.", "76,0%", "51,8%",
             "Margen operativo del 76% en memoria; históricamente irrepetible"],
            ["KLA", "30-34x", "n.d.", "n.d.", "~37%", "~40%",
             "Las mejores economías del equipo, a múltiplo inferior al de Lam"],
            ["Lam Research", "38,1x", "n.d.", "n.d.", "~28%", "~30%",
             "Múltiplo superior con márgenes y retornos inferiores a KLA"],
            ["Applied Materials", "22-32x", "n.d.", "n.d.", "21,5%", "n.d.",
             "El más barato del equipo y también el de menor margen"],
            ["Tokyo Electron", "~28x", "n.d.", "n.d.", "27-30%", "23,0%",
             "Calidad media del grupo; acceso incómodo desde España"],
            ["Synopsys", "35,0x", "n.d.", "n.d.", "41% (aj.)", "2,3%",
             "ROIC hundido por el fondo de comercio de la compra de Ansys"],
            ["Cadence", "n.d.", "n.d.", "n.d.", "44,7% (aj.)", "n.d.",
             "Mismo foso que Synopsys con el balance sin dañar"],
        ],
        [2.3 * cm, 1.5 * cm, 1.9 * cm, 1.6 * cm, 1.5 * cm, 1.3 * cm, 5.9 * cm],
        align_right=(1, 2, 3, 4, 5)))
    s.append(p(
        "Datos públicos recopilados en agosto de 2026. Las fuentes discrepan en "
        "varios casos &mdash; distinta fecha, criterio contable, o línea local "
        "frente a ADR &mdash; y por eso se muestran rangos. (*) El EV/EBITDA de "
        "Broadcom es inconsistente con su PER adelantado; casi con seguridad "
        "mezcla criterios contables. Verificar antes de operar: esto ordena, no "
        "sustituye a la ficha del bróker.", "caption"))
    s.append(chart(chart_roic_vs_pe(), 16.0))
    s.append(p(
        "Cuanto más a la derecha, mejor negocio. Cuanto más abajo, más barato. "
        "La esquina inferior derecha parece el paraíso &mdash; y es justo donde "
        "está la trampa.", "caption"))

    s.append(key_box(
        "La conclusión que ordena todo lo demás",
        "En un sector cíclico, un PER bajo no señala una ganga: señala que el "
        "mercado no cree que ese beneficio se repita. Micron y SK Hynix cotizan "
        "a cuatro y seis veces beneficios con márgenes operativos y brutos en "
        "máximos históricos absolutos. La regla clásica de los cíclicos es "
        "exactamente la contraria a la intuición: <b>se compran con PER alto "
        "&mdash; beneficio deprimido &mdash; y se venden con PER bajo &mdash; "
        "beneficio de pico</b>. Hoy la memoria está en el segundo caso."))
    s.append(PageBreak())

    # -- 3 ------------------------------------------------------------------
    s.append(h1("El caso de la memoria, en detalle", 3))
    s.append(p(
        "Merece sección propia porque es la mayor tentación del sector y el "
        "mayor riesgo de error de un inversor a treinta años.", "lead"))
    s.append(p(
        "SK Hynix reportó un <b>margen operativo del 76% en el segundo trimestre "
        "de 2026</b>, y Micron un margen bruto del 72,6% con crecimiento de "
        "ingresos del 167% y de beneficios de casi el 700%. Para dimensionar lo "
        "que significan esas cifras: la memoria es históricamente el negocio más "
        "brutalmente cíclico del complejo semiconductor, con márgenes de "
        "mitad de ciclo muy inferiores y con trimestres recurrentes de pérdidas "
        "en la parte baja. Un 76% de margen operativo no es un negocio de "
        "memoria: es un negocio de monopolio temporal."))
    s.append(p(
        "La causa es identificable y real: toda la producción de memoria de alto "
        "ancho de banda de 2026 está vendida por contrato en firme, con precio y "
        "volumen cerrados, y la capacidad dedicada a HBM resta obleas a la "
        "memoria convencional, tensionando también ese mercado. Es decir, el "
        "margen extraordinario tiene una explicación estructural, no es un "
        "espejismo contable."))
    s.append(p(
        "Pero una explicación estructural no es lo mismo que una posición "
        "defendible a treinta años. La memoria no tiene el foso de la "
        "litografía ni el de la fundición avanzada: tiene tres competidores "
        "capaces, capacidad que se amplía con capital, y un historial de un "
        "siglo en miniatura de destruir sus propios márgenes en cuanto la "
        "oferta alcanza a la demanda. El contrato en firme de 2026 es una "
        "certeza sobre 2026, no sobre 2032."))
    s.append(warn_box(
        "Cómo tratar la memoria en una cartera de treinta años",
        "No como posición núcleo. Si se quiere exposición, es una posición "
        "satélite, dimensionada para poder perder la mitad sin que altere el "
        "plan, y comprada con la conciencia explícita de que el múltiplo bajo "
        "es la advertencia y no el atractivo. La alternativa intelectualmente "
        "más limpia es capturar el mismo ciclo a través de quien vende el equipo "
        "para fabricar la memoria &mdash; que cobra en las dos direcciones del "
        "ciclo de capacidad &mdash; en lugar de a través del fabricante."))

    # -- 4 ------------------------------------------------------------------
    s.append(h1("Tres modelos de negocio, tres costes de capital distintos", 4))
    s.append(p(
        "El sector se comporta como si fuera uno solo, y en realidad contiene "
        "tres máquinas económicas que no se parecen en nada. Confundirlas es "
        "el error de asignación más caro.", "lead"))
    s.append(table(
        ["Modelo", "Quiénes", "Economía", "Qué múltiplo merece", "Riesgo principal"],
        [
            ["<b>Peaje</b>",
             "ASML, TSMC, KLA, Synopsys, Cadence, Arm",
             "Cobran por cada unidad producida, independientemente de quién gane la carrera. Márgenes altos y estables, retorno sobre capital muy superior al coste de capital.",
             "El más alto, y con razón. La durabilidad justifica pagar.",
             "Pagar tanto por la certeza que el retorno futuro se agote"],
            ["<b>Cíclico de capacidad</b>",
             "Micron, SK Hynix, Samsung, fundición no avanzada",
             "Producto sustituible, precio fijado por el equilibrio de oferta. Márgenes que oscilan entre extraordinarios y negativos.",
             "Bajo en el pico, alto en el valle. Nunca constante.",
             "Comprar el pico creyendo que se compra barato"],
            ["<b>Apalancado</b>",
             "Oracle, CoreWeave y el resto de neonubes",
             "Compran el activo con deuda y lo alquilan. El margen depende del precio de alquiler del cómputo, que es lo primero que cae si sobra capacidad.",
             "El más bajo, y aun así suele estar caro.",
             "Que el coste de la deuda llegue antes que el ingreso"],
        ],
        [2.4 * cm, 3.0 * cm, 4.6 * cm, 3.0 * cm, 3.9 * cm]))

    s.append(h2("El coste, que es la parte que casi nadie mira"))
    s.append(p(
        "La pregunta de a qué coste se está construyendo todo esto tiene una "
        "respuesta concreta y verificable. Oracle cerró su ejercicio 2026 con "
        "<b>55.700 millones de dólares de inversión, flujo de caja libre "
        "negativo de 24.700 millones y una deuda total en el entorno de los "
        "130.000 a 156.000 millones</b>, lo que le costó una rebaja de "
        "calificación crediticia a BBB-, el último escalón antes del grado "
        "especulativo. Guía a unos 70.000 millones de salida neta de caja para "
        "2027."))
    s.append(p(
        "CoreWeave presenta un perfil aún más tenso: apalancamiento bruto sobre "
        "EBITDA en torno a 7 veces, unos 29.000 millones de pasivo frente a "
        "3.900 millones de fondos propios, y flujo de caja libre negativo "
        "previsto hasta 2027 inclusive."))
    s.append(key_box(
        "Dónde se rompería esto primero",
        "No en Nvidia ni en TSMC. Se rompería en el eslabón apalancado, porque "
        "es el único que tiene un calendario de vencimientos que no negocia. "
        "Un fabricante con margen del 60% sobrevive a dos años malos reduciendo "
        "inversión; un arrendador de cómputo con siete veces deuda sobre EBITDA "
        "y flujo negativo, no. Para una cartera de treinta años esto no es un "
        "matiz: es la razón para excluir el bloque entero, por atractiva que "
        "parezca su tasa de crecimiento."))
    s.append(PageBreak())

    # -- 5 ------------------------------------------------------------------
    s.append(h1("La aritmética del retorno, y la variable oculta", 5))
    s.append(p(
        "Dos cálculos sencillos hacen más por entender el riesgo de este sector "
        "que cualquier previsión de mercado total direccionable.", "lead"))

    s.append(h2("Cálculo 1: qué ingreso hace falta para justificar la inversión"))
    s.append(p(
        "El capex acumulado de los hiperescaladores en el trienio 2024&ndash;2026 "
        "se sitúa en el entorno de 1,4 billones de dólares, sumando los "
        "aproximadamente 388.000 millones de 2025 y los 725.000 millones "
        "guiados para 2026. Para obtener un retorno antes de impuestos del 10% "
        "sobre esa base &mdash; que es un listón modesto, por debajo del coste "
        "de capital que exigiría un inversor a estos activos &mdash; harían "
        "falta del orden de 140.000 millones anuales de beneficio operativo "
        "incremental. A un margen operativo del 30%, eso implica del orden de "
        "<b>medio billón de dólares de ingreso anual nuevo</b> atribuible a la "
        "IA."))
    s.append(p(
        "Ese es el número contra el que hay que contrastar cualquier titular. "
        "No es imposible &mdash; es aproximadamente el tamaño actual de todo el "
        "mercado mundial de software empresarial &mdash; pero exige que la IA "
        "no sea una función más dentro de productos existentes, sino una "
        "categoría de gasto nueva de primer orden. Y exige que llegue antes de "
        "que la añada de capex de 2026 termine de amortizarse."))

    s.append(h2("Cálculo 2: la amortización, que es donde se decide el beneficio contable"))
    s.append(p(
        "Los grandes hiperescaladores amortizan servidores en cinco o seis años. "
        "Los chips aceleradores que constituyen el grueso del valor tienen, "
        "según buena parte del análisis independiente, una vida útil económica "
        "sensiblemente menor, con propuestas de amortización por componentes que "
        "asignan entre tres años y medio y cuatro y medio al módulo de proceso y "
        "reservan los seis a ocho años para chasis, red, distribución eléctrica "
        "y refrigeración."))
    s.append(chart(chart_depreciation(), 16.0))
    s.append(p(
        "Efecto sobre la cuenta de resultados de una sola añada de inversión de "
        "725.000 millones, según la vida útil aplicada. Cálculo propio, "
        "amortización lineal sin valor residual.", "caption"))
    s.append(p(
        "La lectura es directa: pasar de seis a cuatro años de vida útil "
        "convierte 121.000 millones de amortización anual en 181.000 millones, "
        "un 50% más, sobre una sola añada de inversión. Y hay una añada nueva "
        "cada ejercicio, cada vez mayor. No cambia la caja &mdash; el dinero ya "
        "se gastó &mdash; pero cambia el beneficio declarado, y por tanto todos "
        "los PER de la tabla de la sección 2."))
    s.append(warn_box(
        "El indicador que hay que vigilar por encima de cualquier otro",
        "No es el precio de las acciones ni los titulares de pedidos. Es <b>la "
        "nota de política contable sobre vida útil de los activos en las "
        "cuentas anuales de los hiperescaladores</b>. Una revisión a la baja de "
        "la vida útil de servidores es la señal más temprana y más fiable de "
        "que el ciclo está madurando, y es pública, gratuita y llega antes que "
        "cualquier revisión de beneficios."))

    # -- 6 ------------------------------------------------------------------
    s.append(h1("Ranking por atractivo de valoración ajustado a calidad", 6))
    s.append(p(
        "Ordenado por lo que pediste: negocio que más gana, sobre menos capital, "
        "al múltiplo menos exigente para esa calidad. No por crecimiento.",
        "lead"))

    W = [2.5 * cm, 1.9 * cm, 1.6 * cm, 11.1 * cm]
    HDR = ["Compañía", "Cotiza en", "PER ad.", "Por qué está en este tier"]

    s += tier_table(0, "TIER 1 &nbsp;&middot;&nbsp; Comprar la calidad, cuidando el precio de entrada",
        HDR, [
        ["TSMC", "NYSE TSM / Taipéi 2330", "19-25x",
         "El mejor binomio del sector: margen operativo del 60,3% y ROIC del 54,6% al múltiplo más bajo de todo el grupo de calidad. Además reinvierte a esa tasa de retorno, que es el motor de compuesto más potente que existe. El riesgo es geopolítico, no económico, y por eso cotiza con descuento."],
        ["ASML", "Ámsterdam ASML", "39x",
         "Monopolio efectivo en litografía extrema y ROIC del 66%. Pero es el múltiplo más alto del sector con el margen operativo más bajo de su tier (36%). La calidad no está en duda; el precio de entrada es toda la discusión. Cotiza en euros, sin fricción de divisa."],
        ["Cadence", "Nasdaq CDNS", "n.d.",
         "Duopolio de EDA con margen operativo ajustado del 44,7% y el balance intacto. Es el nombre del tier con menos peros y por eso rara vez está barato."],
        ["KLA", "Nasdaq KLAC", "30-34x",
         "<b>La anomalía relativa más clara del sector:</b> margen operativo del 37% y ROIC del 40%, mejores que los de Lam Research en ambos casos, y sin embargo cotiza a múltiplo inferior (30-34x frente a 38x). Si hay que elegir un nombre de equipo, la aritmética señala este."],
        ["Nvidia", "Nasdaq NVDA", "22-24x",
         "ROIC del 104,7% y margen bruto del 74,2%: económicamente el mejor negocio de la lista. Y no está caro sobre beneficio adelantado. El problema no es el múltiplo, es que el denominador incorpora unas economías que ningún negocio ha sostenido treinta años."],
    ], W, align_right=(2,))

    s += tier_table(1, "TIER 2 &nbsp;&middot;&nbsp; Buenos negocios con un pero concreto y verificable",
        HDR, [
        ["Synopsys", "Nasdaq SNPS", "35x",
         "Mismo foso que Cadence, pero el ROIC ha caído al 2,3% por el fondo de comercio y la deuda de la compra de Ansys. El negocio operativo sigue intacto (41% de margen ajustado); lo que está dañado es la aritmética del capital. Se arregla con años, no con trimestres."],
        ["Broadcom", "Nasdaq AVGO", "22x",
         "Margen bruto del 67,8% y posición dominante en silicio a medida y red, pero un ROIC del 24,2% que refleja el coste de haber comprado el crecimiento en lugar de generarlo. Múltiplo razonable; calidad de capital inferior a lo que sugiere su reputación."],
        ["Lam Research", "Nasdaq LRCX", "38,1x",
         "Buen negocio (28% de margen, 30% de ROIC) al múltiplo más alto del equipo. Es el caso inverso a KLA: se paga más por menos."],
        ["Applied Materials", "Nasdaq AMAT", "22-32x",
         "El más barato del equipo y también el de menor margen (21,5% de media a cinco años). Consistente: no es una ineficiencia, es un negocio con más exposición a segmentos competidos."],
        ["Tokyo Electron", "Tokio 8035", "~28x",
         "Calidad intermedia (27-30% de margen, 23% de ROIC) sin descuento que lo compense. Acceso poco cómodo desde una cuenta española."],
    ], W, align_right=(2,))

    s += tier_table(2, "TIER 3 &nbsp;&middot;&nbsp; Cíclicos en el pico: múltiplo bajo como advertencia",
        HDR, [
        ["SK Hynix", "Seúl 000660", "4,4x",
         "Margen operativo del 76% y ROIC del 51,8%. Ambas cifras son extraordinarias y ambas son la razón del múltiplo de 4,4x: el mercado las está valorando como transitorias. Capitalización cercana al billón de dólares, ya muy lejos de ser un descubrimiento."],
        ["Micron", "Nasdaq MU", "5,6-6,1x",
         "Margen bruto del 72,6%, ROIC del 67,6%, ingresos +167% y beneficios +693%. Todas las cifras del pico a la vez. Comprar aquí exige creer que la memoria ha cambiado de naturaleza de forma permanente, y esa es una tesis que ha fallado en todos los ciclos anteriores."],
        ["Samsung Electronics", "Seúl 005930", "n.d.",
         "Misma exposición con menos concentración y menos margen; el descuento de conglomerado es real y persistente."],
    ], W, align_right=(2,))

    s += tier_table(3, "TIER 4 &nbsp;&middot;&nbsp; El eslabón apalancado: excluir de una cartera a 30 años",
        HDR, [
        ["Oracle", "NYSE ORCL", "n.d.",
         "Flujo de caja libre de &minus;24.700 millones, deuda de 130.000 a 156.000 millones y rebaja crediticia a BBB-. Guía a 70.000 millones de salida neta en 2027. El crecimiento de la nube es real; el balance que lo financia es el problema."],
        ["CoreWeave", "Nasdaq CRWV", "n.d.",
         "Apalancamiento de 7 veces EBITDA, 29.000 millones de pasivo contra 3.900 de fondos propios, caja libre negativa hasta 2027. Es una opción sobre el precio del alquiler de cómputo financiada con deuda, no una infraestructura."],
        ["Neonubes y arrendadores de GPU", "Varios", "n.d.",
         "Mismo modelo, misma fragilidad. El activo se deprecia rápido, la deuda no."],
    ], W, align_right=(2,))
    s.append(PageBreak())

    # -- 7 ------------------------------------------------------------------
    s.append(h1("Qué comprar, a qué precio y con qué tamaño", 7))
    s.append(p(
        "Pesos dentro de la asignación destinada a este sector. La disciplina de "
        "precio importa aquí más que en ningún otro de los ocho, porque es el "
        "sector donde la calidad es más evidente y por tanto donde más se paga "
        "por ella.", "lead"))
    s.append(table(
        ["Bloque", "Peso", "Nombres", "Precio al que la tesis funciona"],
        [
            ["Peaje de fabricación", "35%", "TSMC",
             "Por debajo de 25x adelantado la relación calidad-precio es favorable con los márgenes actuales. Es el único del sector que hoy no exige contorsiones para justificarlo."],
            ["Peaje de equipo", "20%", "KLA, y ASML por debajo de 32x",
             "KLA es comprable en su rango actual. ASML a 39x exige o bien un horizonte de treinta años sin flaquear, o bien esperar. Construir por tramos, no de una vez."],
            ["Peaje de diseño", "15%", "Cadence, Synopsys en segunda posición",
             "Cadence a cualquier precio razonable; Synopsys solo si se acepta esperar años a que el ROIC se recupere del fondo de comercio."],
            ["Acelerador", "18%", "Nvidia",
             "22-24x adelantado no es exigente. El dimensionamiento debe reflejar que el riesgo está en el beneficio, no en el múltiplo: media posición, y ampliar si el margen bruto se sostiene por encima del 70% dos años más."],
            ["Cíclico de memoria", "0-8%", "Micron o SK Hynix, opcional",
             "Solo como satélite explícito y con la premisa de que se compra un pico. Cero es una respuesta perfectamente válida aquí."],
            ["Apalancado", "0%", "Oracle, CoreWeave, neonubes",
             "Excluido. No supera el test de los cinco años bajo ningún supuesto razonable."],
        ],
        [3.1 * cm, 1.3 * cm, 3.9 * cm, 8.8 * cm], align_right=(1,)))

    s.append(key_box(
        "Solapamiento con lo que ya tienes",
        "TSMC, ASML, Synopsys, Cadence, KLA y Applied Materials ya aparecían en "
        "los informes de semiconductores y de China. <b>No son posiciones "
        "nuevas: son las mismas vistas desde otro ángulo.</b> Lo que aporta este "
        "informe no es ampliar la lista sino ordenarla por precio, y la "
        "conclusión práctica es que la exposición a este sector probablemente ya "
        "esté cubierta y lo que falte sea decidir cuánto y a qué múltiplo. El "
        "documento de consolidación tendrá que restar, no sumar."))

    # -- 8 ------------------------------------------------------------------
    s.append(h1("El test de los cinco años, y qué invalidaría la tesis", 8))
    s.append(p(
        "Si no pudieras tocar la cartera durante cinco años, ¿comprarías esto?",
        "lead"))
    s.append(p(
        "Para el bloque de peaje, sí, y con más tranquilidad que en casi "
        "cualquier otro sector: ASML, TSMC, KLA y Cadence cobran por unidad "
        "producida con independencia de quién gane la carrera de modelos. No "
        "necesitan acertar el ganador. Esa es la definición de un buen activo a "
        "cinco años vista."))
    s.append(p(
        "Para Nvidia, sí pero con media posición. Un ROIC del 105% es una "
        "invitación permanente a la competencia, y sus mayores clientes están "
        "diseñando silicio propio precisamente para dejar de pagarle ese margen. "
        "La posición debe poder sobrevivir a una normalización del margen bruto "
        "sin obligar a vender."))
    s.append(p(
        "Para la memoria y para el bloque apalancado, no. En el primer caso "
        "porque cinco años es tiempo más que suficiente para atravesar un ciclo "
        "completo desde el pico. En el segundo porque el calendario de deuda no "
        "espera a que la tesis madure."))
    s += bullets([
        "<b>Revisión a la baja de la vida útil de servidores</b> en las cuentas "
        "de los hiperescaladores. Es la señal más temprana y la más fiable.",
        "<b>Capex guiado a la baja</b> por dos hiperescaladores en el mismo "
        "trimestre. Uno solo es idiosincrásico; dos es un cambio de régimen.",
        "<b>Margen bruto de Nvidia por debajo del 65%</b> de forma sostenida, "
        "que indicaría que el silicio propio de los clientes está funcionando.",
        "<b>Precio al contado de la memoria en descenso con contratos "
        "renovándose a la baja</b>: el fin del ciclo de la memoria, con un año "
        "de antelación sobre los beneficios.",
        "<b>Un impago o una refinanciación forzada en el eslabón apalancado</b>, "
        "que arrastraría los múltiplos de todo el sector aunque no afecte a los "
        "fundamentales de los peajes. Sería, de hecho, la mejor oportunidad de "
        "compra de la década para el tier 1.",
    ])
    s.append(Spacer(1, 8))
    s.append(key_box(
        "Conclusión",
        "El valor real de este sector no está donde está el crecimiento. Está "
        "en los peajes: TSMC gana un 60% de margen operativo con un 55% de "
        "retorno sobre el capital y cotiza al múltiplo más bajo de todo el grupo "
        "de calidad, y KLA supera a Lam Research en margen y en retorno "
        "cotizando más barato. Lo que parece barato &mdash; memoria a cuatro "
        "veces beneficios &mdash; lo parece porque el beneficio está en máximos "
        "irrepetibles, y lo que financia la fiesta &mdash; el eslabón "
        "apalancado &mdash; es lo primero que rompe si el ingreso llega tarde. "
        "La disciplina de entrada, aquí, vale más que la selección de nombres."))

    s.append(Spacer(1, 12))
    s.append(p(
        "Siguiente en la serie: <b>Sector 3 &mdash; Robótica y automatización "
        "física</b>, con el mismo enfoque de valoración: márgenes, retorno sobre "
        "capital y múltiplo pagado.", "foot"))
    return s


if __name__ == "__main__":
    build(os.path.abspath(OUT),
          "Serie CAGR 30 años  |  Sector 2 de 8  |  Cómputo e infraestructura de IA",
          story())
    print("written:", os.path.abspath(OUT))
