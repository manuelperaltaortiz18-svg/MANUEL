"""Sector 1 of the 30-year CAGR series: electrification and the grid.

Builds electrificacion_red_cadena_valor.pdf — the value chain, where pricing
power actually sits, and the company ranking by tier.
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

OUT = os.path.join(os.path.dirname(__file__), "..",
                   "electrificacion_red_cadena_valor.pdf")
TMP = os.environ.get("SCRATCH", "/tmp")

PLOT_INK = "#141821"
PLOT_ACCENT = "#1F6F8B"
PLOT_MUTED = "#8C97A3"


def _style_axes(ax):
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color("#C9D2DB")
    ax.tick_params(colors="#5A6472", labelsize=8)
    ax.set_axisbelow(True)


# --------------------------------------------------------------------------
# Chart 1 — the roadmap: revenue growth against how much of it investors keep
# --------------------------------------------------------------------------

def chart_roadmap():
    # (sector, est. revenue CAGR %, est. value capture 0-100, order in series)
    pts = [
        ("Electrificación y red",        8.5, 88, 1),
        ("Cómputo e infra de IA",       19.0, 72, 2),
        ("Robótica y automatización",   15.5, 58, 3),
        ("Biotecnología metabólica",    12.0, 62, 4),
        ("Nuclear y ciclo de combustible", 14.0, 49, 5),
        ("Ciberseguridad",              11.5, 78, 6),
        ("Agua y escasez de recursos",   6.5, 82, 7),
        ("Economía espacial",           14.5, 44, 8),
    ]
    fig, ax = plt.subplots(figsize=(9.2, 5.4), dpi=200)
    _style_axes(ax)

    for name, cagr, capture, order in pts:
        size = 430 if order <= 2 else 300
        color = PLOT_ACCENT if order <= 2 else "#7FAEBE"
        ax.scatter(cagr, capture, s=size, color=color, zorder=3,
                   edgecolor="white", linewidth=1.6)
        ax.annotate(str(order), (cagr, capture), color="white", fontsize=9,
                    weight="bold", ha="center", va="center", zorder=4)
        ax.annotate(name, (cagr, capture), textcoords="offset points",
                    xytext=(0, -20), ha="center", fontsize=7.6,
                    color=PLOT_INK)

    # The diagonal marks equal expected investor outcome: high growth with
    # low capture lands in the same place as modest growth investors keep.
    ax.axhline(70, color=PLOT_MUTED, lw=0.8, ls="--", zorder=1)
    ax.annotate("umbral de captura defendible", (4.4, 71.2), fontsize=7,
                color=PLOT_MUTED, ha="left")

    ax.set_xlabel("Crecimiento estimado de ingresos del sector, CAGR 2026-2056 (%)",
                  fontsize=8.5, color=PLOT_INK)
    ax.set_ylabel("Captura de valor por el accionista (índice 0-100)",
                  fontsize=8.5, color=PLOT_INK)
    ax.set_xlim(4, 21)
    ax.set_ylim(35, 97)
    ax.grid(axis="both", color="#E4EAEF", lw=0.7)
    fig.tight_layout()
    path = os.path.join(TMP, "roadmap.png")
    fig.savefig(path, facecolor="white")
    plt.close(fig)
    return path


# --------------------------------------------------------------------------
# Chart 2 — the bottleneck that creates the pricing power
# --------------------------------------------------------------------------

def chart_lead_times():
    years = ["2019", "2021", "2023", "2025", "2026"]
    large_tx = [12, 20, 40, 52, 55]      # large power transformers, months
    hv_cable = [14, 22, 36, 48, 50]      # HV subsea/land cable, months
    switchgear = [8, 12, 24, 34, 36]     # HV switchgear, months

    fig, ax = plt.subplots(figsize=(9.2, 4.2), dpi=200)
    _style_axes(ax)
    ax.plot(years, large_tx, marker="o", lw=2.2, color=PLOT_ACCENT,
            label="Transformadores de potencia")
    ax.plot(years, hv_cable, marker="s", lw=2.2, color="#3E8FA6",
            label="Cable de alta tensión")
    ax.plot(years, switchgear, marker="^", lw=2.2, color="#A9BAC6",
            label="Aparamenta de AT")
    ax.set_ylabel("Plazo de entrega (meses)", fontsize=8.5, color=PLOT_INK)
    ax.grid(axis="y", color="#E4EAEF", lw=0.7)
    ax.legend(frameon=False, fontsize=8, loc="upper left")
    ax.set_ylim(0, 62)
    fig.tight_layout()
    path = os.path.join(TMP, "leadtimes.png")
    fig.savefig(path, facecolor="white")
    plt.close(fig)
    return path


# --------------------------------------------------------------------------
# Story
# --------------------------------------------------------------------------

def story():
    s = []
    s += cover(
        "Electrificación<br/>y red eléctrica",
        "El cuello de botella físico que convierte<br/>"
        "un sector aburrido en el mejor compuesto a 30 años",
        "SERIE CAGR 30 AÑOS &nbsp;&middot;&nbsp; SECTOR 1 DE 8",
        [("Horizonte", "2026 - 2056"),
         ("Compañías analizadas", "64"),
         ("Método", "Cadena de valor + captura de valor + acceso fiscal ES"),
         ("Fecha", "Agosto 2026")],
    )

    # -- 0. The series ------------------------------------------------------
    s.append(h1("Los ocho sectores de la serie, y por qué en este orden", 0))
    s.append(p(
        "El encargo era identificar los sectores con mayor CAGR a 30 años. La "
        "respuesta honesta empieza corrigiendo la pregunta: <b>el CAGR de "
        "ingresos de un sector y el CAGR del inversor que lo compra son dos "
        "cosas distintas, y con frecuencia van en direcciones opuestas.</b> "
        "Las aerolíneas, la automoción, las telecos de los 2000 y los paneles "
        "solares crecieron espectacularmente y arruinaron a sus accionistas. "
        "El crecimiento, sin barrera de entrada, se lo queda el cliente y el "
        "competidor nuevo.", "lead"))
    s.append(p(
        "Por eso la serie no ordena por crecimiento bruto, sino por el producto "
        "de tres cosas: crecimiento estructural, capacidad de capturarlo, y "
        "durabilidad de esa captura a lo largo de tres décadas. El gráfico "
        "sitúa los ocho sectores en ese plano."))
    s.append(chart(chart_roadmap(), 16.2))
    s.append(p(
        "Estimaciones propias de rango central; las barras de error reales son "
        "amplias y el eje vertical es un juicio cualitativo, no un dato "
        "observable. Sirve para ordenar, no para valorar.", "caption"))

    s.append(table(
        ["#", "Sector", "Motor estructural de 30 años", "Por qué captura (o no)"],
        [
            ["1", "Electrificación y red",
             "Demanda eléctrica en escalón: transporte, calor, industria y centros de datos",
             "Oligopolio consolidado, base instalada con servicio recurrente, cuello de botella físico"],
            ["2", "Cómputo e infraestructura de IA",
             "Gasto de capital sostenido en cómputo, memoria, red y refrigeración",
             "Captura altísima en el cuello (litografía, EDA, HBM), destructiva en el resto"],
            ["3", "Robótica y automatización física",
             "Escasez laboral estructural y envejecimiento demográfico",
             "Captura desigual: fuerte en actuación y visión, débil en integración"],
            ["4", "Biotecnología metabólica y longevidad",
             "Obesidad, diabetes, oncología y demografía envejecida",
             "Márgenes extraordinarios con fecha de caducidad: el precipicio de patentes"],
            ["5", "Nuclear y ciclo de combustible",
             "Carga base libre de carbono; reactores modulares y enriquecimiento",
             "Cuello real en combustible y enriquecimiento; los constructores capturan poco"],
            ["6", "Ciberseguridad y confianza digital",
             "Superficie de ataque creciente y regulación obligatoria",
             "Ingreso recurrente, coste de cambio alto, presupuesto no discrecional"],
            ["7", "Agua y complejo de escasez",
             "Estres hidrico, reposición de redes, tratamiento",
             "Cuasi monopolios locales y regulación protectora; crecimiento modesto"],
            ["8", "Economía espacial",
             "Lanzamiento barato, constelaciones, observación terrestre",
             "Captura hoy concentrada en un actor no cotizado; el resto quema capital"],
        ],
        [0.8 * cm, 3.5 * cm, 5.6 * cm, 6.6 * cm], align_right=(0,)))

    s.append(key_box(
        "El motivo de que la electrificación vaya primera y no la IA",
        "El cómputo de IA crece más del doble de rápido. Pero su captura está "
        "concentrada en cuatro o cinco empresas que ya analizamos en los "
        "informes de semiconductores y China, y su tasa de crecimiento depende "
        "de un ciclo de inversión que puede pausarse. La electrificación crece "
        "menos, pero lo hace contra una restricción física &mdash; no hay "
        "suficientes fabricas de transformadores ni electricistas en el mundo "
        "&mdash; y esa restricción la explotan un oligopolio de seis nombres que "
        "lleva treinta años consolidándose. Menos crecimiento, más del "
        "crecimiento retenido, durante más tiempo."))
    s.append(PageBreak())

    # -- 1. Thesis ----------------------------------------------------------
    s.append(h1("La tesis en una página", 1))
    s.append(p(
        "Durante veinticinco años la demanda eléctrica de las economias "
        "desarrolladas fue plana. La eficiencia compensaba el crecimiento, y "
        "la red se gestionaba como un activo maduro en mantenimiento mínimo. "
        "Ese régimen ha terminado, y ha terminado por cuatro razones "
        "simultáneas que no dependen unas de otras.", "lead"))
    s.append(h2("Los cuatro motores, y por qué son independientes"))
    s += bullets([
        "<b>Transporte.</b> Cada vehículo electrificado traslada energía del "
        "surtidor a la red. Es demanda nueva sobre infraestructura de "
        "distribución que no se dimensionó para ella, y llega barrio a barrio, "
        "obligando a reforzar el último kilómetro.",
        "<b>Calor.</b> Bombas de calor sustituyendo caldera de gas. Mismo "
        "efecto, pero concentrado en el pico invernal, que es exactamente "
        "donde la red tiene menos holgura.",
        "<b>Industria.</b> Electrificación de procesos térmicos, más la "
        "relocalización de manufactura hacia Norteamerica y Europa. Cada "
        "fabrica nueva es una acometida de alta tensión.",
        "<b>Centros de datos.</b> El motor más rápido y el más volátil. "
        "Concentra decenas o centenas de megavatios en un solo punto, con un "
        "plazo de conexión que hoy es el principal límite físico al despliegue "
        "de capacidad de cómputo.",
    ])
    s.append(p(
        "La independencia importa más que la magnitud. Si la inversión en IA se "
        "enfría, los otros tres motores siguen. Si Europa desacelera, la "
        "reposición de red norteamericana &mdash; con una edad media de activo "
        "que supera holgadamente su vida de diseño &mdash; continua por pura "
        "obsolescencia. Es una demanda con cuatro patas, y hacen falta varias "
        "roturas simultáneas para tumbarla."))

    s.append(h2("Pero la demanda no es la tesis. La restricción lo es."))
    s.append(p(
        "Que un sector tenga demanda creciente no genera retorno. Lo genera que "
        "la oferta no pueda responder. Y aquí la oferta no puede responder, por "
        "un motivo poco glamuroso: <b>no hay fábricas, no hay acero eléctrico y "
        "no hay electricistas.</b>"))
    s.append(chart(chart_lead_times(), 16.2))
    s.append(p(
        "Plazos de entrega típicos de mercado; varían mucho por tensión, "
        "potencia y cliente. La forma de la curva importa más que el nivel.",
        "caption"))
    s.append(p(
        "Un transformador de potencia grande se pide hoy con cuatro años y medio "
        "de antelación. Eso no es una anomalía logística de la pandemia: es "
        "estructural. Los fabricantes se quemaron con la sobrecapacidad de la "
        "década de 2010, cuando la demanda plana y la entrada de competidores "
        "hundieron los precios durante años. La consecuencia es que hoy amplían "
        "capacidad con extrema prudencia, con contratos en firme y prepago, no "
        "en anticipación de la demanda. Están gestionando el negocio para "
        "margen, no para cuota."))
    s.append(key_box(
        "La asimetría que hace investible el sector",
        "La demanda es un escalón estructural de treinta años. La oferta se "
        "amplia con la cautela de quien recuerda el ciclo anterior y esta "
        "limitada por el acero eléctrico de grano orientado, cuya capacidad "
        "mundial esta en muy pocas manos. Mientras esa brecha persista, el "
        "poder de fijación de precios se queda en el fabricante de equipo. La "
        "pregunta de inversión no es si la demanda existe &mdash; existe "
        "&mdash;, sino cuántos años tarda la oferta en alcanzarla. Ese es el "
        "verdadero reloj de esta tesis, y a él está dedicada la sección 7."))
    s.append(PageBreak())

    # -- 2. Value chain -----------------------------------------------------
    s.append(h1("La cadena de valor, y dónde se queda el dinero", 2))
    s.append(p(
        "El error habitual del inversor minorista en este tema es comprar la "
        "eléctrica. Es intuitivo &mdash; la eléctrica vende la electricidad "
        "&mdash; y es casi siempre el peor punto de entrada de toda la cadena.",
        "lead"))
    s.append(table(
        ["Eslabón", "Qué hace", "Poder de precio", "Margen tipico", "Veredicto"],
        [
            ["Materia prima eléctrica",
             "Acero de grano orientado, cobre, aluminio, resinas",
             "Alto en acero GO, nulo en cobre", "Variable",
             "Selectivo: el acero GO si, el cobre es precio-aceptante"],
            ["Equipo primario",
             "Transformadores, aparamenta, cable de AT, HVDC",
             "Muy alto hoy", "Expandiéndose",
             "<b>El mejor sitio de la cadena</b>"],
            ["Equipo secundario y distribución",
             "Cuadros BT, canalización, protección, conectividad",
             "Alto y estable", "Alto y estable",
             "<b>Excelente: menos cíclico y con base instalada</b>"],
            ["Ingeniería y construcción",
             "Tendido, subestaciones, conexión de cliente",
             "Alto por escasez de mano de obra", "Medio",
             "Bueno mientras falte personal cualificado"],
            ["Propietario del activo (eléctrica regulada)",
             "Posee y opera la red, cobra tarifa",
             "Nulo: el retorno lo fija el regulador", "Regulado",
             "Cobra crecimiento de base de activos, no margen"],
            ["Generación comercial",
             "Vende energía en mercado o por contrato",
             "Cíclico, dependiente del precio mayorista", "Volátil",
             "Es una apuesta de precio, no de infraestructura"],
            ["Software y medición",
             "Contadores, gestión de red, simulación",
             "Alto, coste de cambio elevado", "Muy alto",
             "Bueno, pero mercado pequeño frente al equipo"],
        ],
        [2.9 * cm, 3.6 * cm, 2.9 * cm, 2.2 * cm, 4.9 * cm]))

    s.append(warn_box(
        "Por qué la eléctrica regulada decepciona en esta tesis",
        "Una eléctrica regulada no gana más porque la electricidad escasee: su "
        "retorno sobre base de activos lo fija el regulador, y si los beneficios "
        "se disparan, el regulador lo corrige. Lo que si obtiene es crecimiento "
        "de la base de activos &mdash; invierte más, y gana ese retorno fijo "
        "sobre una base mayor. Es un compuesto real, pero modesto y apalancado, "
        "y además es quien <b>paga</b> los precios crecientes del equipo. En "
        "esta cadena, la eléctrica es el cliente cautivo. El accionista quiere "
        "estar del lado del proveedor."))

    s.append(h2("El cuello dentro del cuello: el acero eléctrico de grano orientado"))
    s.append(p(
        "Todo transformador necesita núcleo de acero de grano orientado, un "
        "material con una metalurgia exigente que fabrican muy pocas plantas en "
        "el mundo. No es un producto que se pueda improvisar: una línea nueva "
        "lleva años y un capital considerable, y el mercado histórico era "
        "demasiado pequeño y demasiado cíclico para justificarlo. Esa es la "
        "razón física última de que los plazos de entrega de transformadores no "
        "bajen. Cualquiera que quiera saber cuándo termina esta ventana debe "
        "vigilar los anuncios de capacidad de acero GO, no los de "
        "transformadores."))
    s.append(PageBreak())

    # -- 3. Ranking ---------------------------------------------------------
    s.append(h1("Ranking de compañías por insustituibilidad", 3))
    s.append(p(
        "Mismo criterio que en los informes anteriores: la puntuación mide cuán "
        "difícil seria sustituir a la compañía si desapareciera mañana, no su "
        "crecimiento reciente ni su valoración. Es deliberadamente insensible "
        "al momentum.", "lead"))

    W = [3.4 * cm, 2.0 * cm, 1.5 * cm, 9.1 * cm]
    HDR = ["Compañía", "Cotiza en", "Punt.", "Por qué ocupa ese lugar"]

    s += tier_table(0, "TIER 1 &nbsp;&middot;&nbsp; Cuellos de botella reales (85-95)",
        HDR, [
        ["Hitachi Energy (vía Hitachi)", "Tokio 6501", "95",
         "Líder mundial en corriente continua de alta tensión, la tecnología sin alternativa para transporte masivo a larga distancia y conexión de eólica marina. Cartera de pedidos que cubre años."],
        ["Schneider Electric", "París SU", "94",
         "El nombre mejor posicionado de la cadena: distribución eléctrica más gestión de energía de centro de datos, con base instalada enorme y servicio recurrente. Euro, sin fricción de divisa."],
        ["Siemens Energy", "Frankfurt ENR", "92",
         "División de red con cartera de pedidos récord y capacidad de HVDC. Historia operativa accidentada por eólica, lo que ha sido a la vez el riesgo y la oportunidad."],
        ["Eaton", "NYSE ETN", "92",
         "Gestión de potencia con exposición directa al centro de datos y a la reindustrialización norteamericana. Ejecución consistentemente superior a la media del grupo."],
        ["ABB", "Zurich ABBN", "90",
         "Electrificación y automatización con márgenes que han mejorado de forma sostenida tras años de reestructuración."],
        ["Prysmian", "Milán PRY", "90",
         "Mayor cablista del mundo tras absorber a Encore Wire; el cable submarino de alta tensión es un oligopolio de tres."],
        ["Quanta Services", "NYSE PWR", "89",
         "No fabrica nada: posee la plantilla cualificada que tiende la línea. En un mundo sin electricistas suficientes, esa es la restricción más difícil de replicar de todas."],
        ["NKT", "Copenhague NKT", "88",
         "Cable submarino de AT, uno de los tres del oligopolio, con capacidad vendida por adelantado durante años."],
        ["GE Vernova", "NYSE GEV", "88",
         "Turbinas de gas y equipo de red. La turbina de gas ha pasado de activo en declive estructural a cuello de botella por la demanda firme de centros de datos."],
        ["Vertiv", "NYSE VRT", "86",
         "Potencia y refrigeración dentro del centro de datos. Crecimiento superior al del grupo, pero también la mayor dependencia de un solo motor de demanda."],
        ["Nexans", "París NEX", "86",
         "Reenfocada con éxito de cable general a alta tensión y submarino. Transformación ya reconocida por el mercado."],
        ["Legrand", "París LR", "85",
         "Infraestructura eléctrica de edificio. Menos espectacular, más defensiva, y con un historial de asignación de capital notablemente disciplinado."],
    ], W, align_right=(2,))

    s += tier_table(1, "TIER 2 &nbsp;&middot;&nbsp; Sólidas con foso claro (72-84)",
        HDR, [
        ["Hubbell", "NYSE HUBB", "83", "Componentes de red para las eléctricas norteamericanas; producto especificado y homologado, lo que hace lenta la sustitución."],
        ["Hyosung Heavy", "Seul 298040", "82", "Transformadores de potencia con exposición directa a la reposición norteamericana. Acceso complicado desde una cuenta española."],
        ["HD Hyundai Electric", "Seul 267260", "81", "Igual tesis que Hyosung; ambas son la válvula de escape de la escasez occidental de transformadores."],
        ["nVent Electric", "NYSE NVT", "80", "Protección y conexión eléctrica, con refrigeración líquida para centro de datos como opción de crecimiento."],
        ["Siemens AG", "Frankfurt SIE", "80", "Exposicion indirecta y diluida por automatización y software; menos pura, pero más estable."],
        ["Rockwell Automation", "NYSE ROK", "78", "Automatización industrial ligada a la relocalización de manufactura; más cíclica de lo que sugiere su reputación."],
        ["Mitsubishi Electric", "Tokio 6503", "78", "Transformadores y aparamenta con posición asiática sólida y gobernanza en mejora lenta."],
        ["Atkore", "NYSE ATKR", "75", "Canalización eléctrica. Muy expuesta a la normalización de precios tras el ciclo extraordinario; el caso bajista es real."],
        ["Powell Industries", "Nasdaq POWL", "75", "Aparamenta a medida, con cartera fuerte pero tamaño pequeño y concentración de clientes."],
        ["LS Electric", "Seul 010120", "74", "Equipo de red coreano con creciente exportación a Norteamerica."],
        ["Fuji Electric", "Tokio 6504", "73", "Electrónica de potencia y semiconductor de potencia; solapamiento útil con el informe de semiconductores."],
        ["AMETEK", "NYSE AME", "72", "Instrumentación eléctrica de nicho; compuesto excelente históricamente, exposición temática indirecta."],
    ], W, align_right=(2,))

    s += tier_table(2, "TIER 3 &nbsp;&middot;&nbsp; La restricción material (selectivo)",
        HDR, [
        ["Nippon Steel", "Tokio 5401", "79", "Uno de los mayores productores de acero de grano orientado. Es el cuello de botella físico real, aunque enterrado dentro de una siderúrgica cíclica."],
        ["JFE Holdings", "Tokio 5411", "74", "Segundo productor japonés de acero GO; misma lógica, mismo problema de dilución dentro del conglomerado."],
        ["POSCO Holdings", "Seul 005490", "70", "Acero GO con ambición de ampliar capacidad; vigilar sus anuncios como señal de fin de ciclo."],
        ["Cleveland-Cliffs", "NYSE CLF", "66", "Único productor integrado de acero GO en Norteamerica, lo que le da relevancia política; balance y ciclicidad son el riesgo."],
        ["Freeport-McMoRan", "NYSE FCX", "70", "Cobre. La electrificación es intensiva en cobre, pero el productor es precio-aceptante: gana si el precio sube, no por ser insustituible."],
        ["Southern Copper", "NYSE SCCO", "68", "Reservas de cobre excepcionales y coste bajo; riesgo político y de gobernanza elevado."],
        ["Antofagasta", "Londres ANTO", "66", "Cobre chileno cotizado en Londres; acceso cómodo desde Europa."],
        ["Ivanhoe Mines", "Toronto IVN", "62", "Uno de los mejores activos de cobre no desarrollados del mundo, con riesgo jurisdiccional acorde."],
    ], W, align_right=(2,))

    s += tier_table(3, "TIER 4 &nbsp;&middot;&nbsp; Propietarios del activo: el lado equivocado, con matices",
        HDR, [
        ["Iberdrola", "Madrid IBE", "72", "Redes reguladas diversificadas por geografía y con gestión probada. Para un residente fiscal español no hay retención extranjera, lo que mejora materialmente el rendimiento neto del dividendo."],
        ["NextEra Energy", "NYSE NEE", "71", "Combina red regulada en Florida con la mayor cartera renovable; el mejor historial de crecimiento del sector."],
        ["Constellation Energy", "Nasdaq CEG", "70", "Nuclear existente vendida por contrato a hiperescaladores. Es la forma más limpia de comprar 'electrón firme escaso'; ya muy reconocida por el mercado."],
        ["Redeia", "Madrid RED", "62", "Operador del sistema español; monopolio puro y rendimiento alto, pero crecimiento limitado por el marco retributivo."],
        ["Enel", "Milán ENEL", "64", "Mayor operador de red de distribución de Europa; historia de reducción de deuda tras años de expansión."],
        ["National Grid", "Londres NG", "66", "Transporte puro en Reino Unido y noreste de EE UU; el caso más limpio de crecimiento de base de activos, con ampliaciones de capital como riesgo recurrente."],
        ["Terna", "Milán TRN", "63", "Transporte italiano, plan de inversión elevado y visibilidad regulatoria buena."],
        ["Sempra / AEP / Southern", "NYSE", "60-66", "Eléctricas norteamericanas con fuerte crecimiento de base de activos; válidas como renta, no como motor de compuesto."],
    ], W, align_right=(2,))

    s += tier_table(4, "TIER 5 &nbsp;&middot;&nbsp; Adyacentes: mayor crecimiento, captura mucho más dudosa",
        HDR, [
        ["Fluence Energy", "Nasdaq FLNC", "48", "Integrador de almacenamiento; ensambla celdas que no fabrica, con margen fino y competencia china directa."],
        ["Enphase / SolarEdge", "Nasdaq", "40-45", "Electrónica solar residencial. Ejemplo de manual de crecimiento sectorial sin foso: la competencia devoró el margen."],
        ["Itron", "Nasdaq ITRI", "62", "Medición inteligente y software de red; coste de cambio real, mercado pequeño."],
        ["Bentley Systems", "Nasdaq BSY", "68", "Software de ingeniería de infraestructura; suscripcion pegajosa y valoración consecuentemente exigente."],
        ["Generac", "NYSE GNRC", "52", "Generación de respaldo; demanda ligada a la fragilidad de la red, pero muy dependiente del clima y del consumidor."],
        ["Bloom Energy", "NYSE BE", "44", "Pilas de combustible para alimentación in situ de centros de datos; opcionalidad real, economía aún no demostrada."],
        ["Sungrow / CATL", "Shenzhen", "70-80", "Inversores y baterías chinos. Dominantes y baratos, pero sujetos a las restricciones descritas en el informe de China."],
    ], W, align_right=(2,))
    s.append(PageBreak())

    # -- 4. Overlap ---------------------------------------------------------
    s.append(h1("Solapamiento con lo que ya tienes analizado", 4))
    s.append(p(
        "Este es el punto que planteaba al cerrar la serie anterior, y conviene "
        "resolverlo ahora y no al final, porque afecta a como se construye la "
        "cartera de cada sector.", "lead"))
    s.append(table(
        ["Nombre", "Aparece también en", "Como tratarlo"],
        [
            ["CATL", "China tech (Tier 2)",
             "Una sola posición. Comprarla dos veces por dos tesis distintas sigue siendo una sola apuesta."],
            ["Fuji Electric, Mitsubishi Electric", "Semiconductores (potencia)",
             "Solapamiento parcial y benigno; el semiconductor de potencia es justamente el nexo entre ambos temas."],
            ["Siemens AG", "Defensa (electrónica)",
             "Exposicion diluida en los dos informes; no justifica doble peso."],
            ["GE Vernova", "Defensa (Vía GE Aerospace, distinta entidad)",
             "Sociedades separadas desde la escisión; no hay solapamiento real."],
            ["Constellation, Vistra", "Aparecera en Nuclear (sector 5)",
             "Decidir allí, no aquí: la tesis nuclear es más específica que la de red."],
        ],
        [3.4 * cm, 4.2 * cm, 9.4 * cm]))
    s.append(key_box(
        "Regla para toda la serie",
        "Cuando terminemos los ocho sectores, la union de las carteras "
        "individuales <b>no</b> es la cartera final. Habra que consolidar, "
        "eliminar duplicados y comprobar que la diversificación aparente por "
        "sectores no esconde una única apuesta concentrada en equipo de "
        "semiconductores y electrificación. Ese es el trabajo del documento de "
        "cierre."))

    # -- 5. Access ----------------------------------------------------------
    s.append(h1("Acceso desde España y coste fiscal", 5))
    s.append(p(
        "Este sector tiene una ventaja poco comentada para un inversor español: "
        "<b>una parte inusualmente grande de los mejores nombres cotiza en "
        "euros.</b> Schneider, Legrand y Nexans en París; Prysmian y Enel en "
        "Milán; Siemens Energy en Frankfurt; NKT en Copenhague; Iberdrola y "
        "Redeia en Madrid. No hay fricción de cambio de divisa ni riesgo de "
        "tipo sobre una posición de treinta años."))
    s.append(table(
        ["Vía", "Que resuelve", "Coste y fricción", "Cuando usarla"],
        [
            ["Acciones en euros (París, Milán, Madrid, Frankfurt)",
             "Núcleo de la cartera del sector",
             "Comisión por operación; retención en origen según país, recuperable por convenio",
             "Preferente. Es la Vía más limpia y barata a largo plazo."],
            ["Acciones en Madrid (Iberdrola, Redeia)",
             "Exposicion sin retención extranjera",
             "Solo retención española, ya a cuenta del IRPF",
             "Óptima fiscalmente, pero es el eslabón regulado: peso limitado."],
            ["Acciones estadounidenses (ETN, PWR, GEV, VRT, HUBB)",
             "Los nombres sin equivalente europeo",
             "Retención del 15% con W-8BEN presentado; exposición al dolar",
             "Necesaria: Quanta y Eaton no tienen sustituto europeo."],
            ["Fondo traspasable de infraestructura o utilities",
             "Diferimiento fiscal entre fondos",
             "Comisión de gestión superior; ningún fondo replica esta tesis con precisión",
             "Util para la parte que quieras poder reasignar sin tributar."],
            ["ETF temático de red o infraestructura limpia",
             "Diversificación instantánea",
             "Suelen mezclar equipo con eléctricas y con solar, diluyendo la tesis",
             "Poco recomendable aquí: el ETF compra justo el eslabón equivocado."],
        ],
        [3.9 * cm, 3.4 * cm, 4.6 * cm, 5.1 * cm]))
    s.append(warn_box(
        "Sobre los fondos traspasables",
        "El artículo 94 de la Ley del IRPF permite traspasar entre fondos sin "
        "tributar la plusvalía, y eso es una ventaja compuesta real a treinta "
        "años. Pero no existe hoy un fondo que capture esta tesis con precisión: "
        "los productos de infraestructura cotizada están dominados por "
        "eléctricas reguladas y concesiones de autopistas, es decir, "
        "exactamente el eslabón de menor captura. Comprar el ETF temático es "
        "comprar al cliente en lugar de al proveedor."))

    # -- 6. Portfolio -------------------------------------------------------
    s.append(h1("Construcción de cartera del sector", 6))
    s.append(p(
        "Pesos relativos <i>dentro</i> de la asignación que decidas destinar a "
        "este sector, no sobre la cartera total. La asignación global se fija en "
        "el documento de consolidación, cuando estén los ocho.", "lead"))
    s.append(table(
        ["Bloque", "Peso", "Nombres", "Función en la cartera"],
        [
            ["Núcleo de equipo eléctrico", "40%",
             "Schneider, Eaton, ABB, Legrand",
             "El compuesto principal. Base instalada, servicio recurrente, oligopolio maduro."],
            ["Cuello de alta tensión", "22%",
             "Hitachi, Siemens Energy, Prysmian o NKT",
             "Donde el poder de precio es más agudo hoy; también lo más cíclico."],
            ["Restricción de mano de obra", "12%",
             "Quanta Services",
             "La escasez más difícil de resolver con capital. Sin equivalente europeo."],
            ["Centro de datos", "10%",
             "Vertiv, GE Vernova",
             "Mayor crecimiento y mayor dependencia de un solo motor. Peso deliberadamente contenido."],
            ["Restricción material", "8%",
             "Nippon Steel o POSCO",
             "Exposicion al acero GO; aceptando que llega envuelta en una siderúrgica cíclica."],
            ["Ancla regulada", "8%",
             "Iberdrola",
             "Renta, estabilidad y eficiencia fiscal doméstica; contrapeso a la ciclicidad del resto."],
        ],
        [3.9 * cm, 1.5 * cm, 4.3 * cm, 7.3 * cm], align_right=(1,)))

    # -- 7. Risks -----------------------------------------------------------
    s.append(h1("Qué invalidaría esta tesis", 7))
    s.append(p(
        "Ordenados por probabilidad, no por gravedad. Los tres primeros son "
        "escenarios plausibles, no colas remotas.", "lead"))
    s += bullets([
        "<b>La oferta alcanza a la demanda (el riesgo central).</b> Es el reloj "
        "de todo el argumento. La señal adelantada no son los transformadores "
        "sino el acero de grano orientado: cuando se anuncien líneas nuevas de "
        "capacidad significativa, la ventana de precios empieza a cerrarse con "
        "dos o tres años de retraso. Vigilar también la normalización de los "
        "plazos de entrega por debajo de veinticuatro meses.",
        "<b>La valoración ya lo descuenta.</b> Este es el riesgo más inmediato. "
        "Buena parte de estos nombres han pasado de múltiplos de industrial "
        "aburrido a múltiplos de crecimiento. La tesis puede ser correcta y el "
        "retorno mediocre si se paga la certeza. Aquí la disciplina de entrada "
        "importa más que en cualquiera de los otros siete sectores.",
        "<b>Digestion del ciclo de centros de datos.</b> Una pausa en el gasto "
        "de capital de IA no rompe la tesis &mdash; quedan tres motores &mdash; "
        "pero si comprimiría severamente los múltiplos de los nombres más "
        "expuestos, Vertiv en primer lugar. Es la razón de que su peso "
        "propuesto sea bajo.",
        "<b>Entrada china en el equipo occidental.</b> Los fabricantes chinos de "
        "transformadores y aparamenta tienen capacidad y precio. Su exclusión "
        "de las redes occidentales es hoy una decisión política de seguridad, no "
        "una limitación técnica. Si esa política se relaja por urgencia de "
        "suministro, el oligopolio se estrecha.",
        "<b>Reacción regulatoria.</b> Si el coste del equipo empuja la factura "
        "eléctrica lo bastante arriba, la respuesta política recae sobre la "
        "eléctrica regulada, que a su vez presiona al proveedor. Es un riesgo "
        "lento y de segundo orden, pero real en un horizonte de décadas.",
    ])

    # -- 8. Five-year test --------------------------------------------------
    s.append(h1("El test de los cinco años", 8))
    s.append(p(
        "La pregunta obligada del sistema: si no pudieras tocar la posición "
        "durante cinco años, ¿La comprarías igual?", "lead"))
    s.append(p(
        "Para el núcleo de equipo eléctrico, la respuesta es sí con bastante "
        "claridad. Son negocios con base instalada, ingreso de servicio "
        "recurrente, retorno sobre capital alto y una estructura competitiva que "
        "lleva tres décadas consolidándose en lugar de fragmentarse. Sobreviven "
        "a un error de calendario porque el activo sigue componiendo mientras "
        "esperas."))
    s.append(p(
        "Para el cuello de alta tensión la respuesta es sí, pero con menos "
        "convicción: son negocios de cartera de pedidos, y una cartera de "
        "pedidos es una foto de la demanda pasada. Cinco años es tiempo "
        "suficiente para atravesar un ciclo completo de contratación."))
    s.append(p(
        "Para el bloque de centro de datos, la respuesta honesta es que no "
        "supera el test con el mismo peso que los demás. Por eso está en la "
        "cartera con un diez por ciento y no con un treinta: es donde el "
        "crecimiento es mayor y donde la visibilidad a cinco años es menor. "
        "Es exactamente el tipo de posición que el sistema pide dimensionar por "
        "convicción y no por entusiasmo."))
    s.append(Spacer(1, 10))
    s.append(key_box(
        "Conclusión",
        "La electrificación no es el sector de mayor crecimiento de los ocho, y "
        "esa es precisamente la razón de que encabece la lista. Combina una "
        "demanda con cuatro motores independientes, una restricción de oferta "
        "física y lenta de resolver, y un grupo de proveedores que ya demostró "
        "durante la década pasada que prefiere margen a cuota. El riesgo real "
        "no es que la tesis sea falsa, sino que sea tan evidente que ya este "
        "pagada. La respuesta a eso es disciplina de precio de entrada y "
        "construcción escalonada, no renunciar al sector."))

    s.append(Spacer(1, 14))
    s.append(p(
        "Siguiente en la serie: <b>Sector 2 &mdash; Cómputo e infraestructura de "
        "IA</b>, donde el crecimiento es el doble y la pregunta interesante deja "
        "de ser si el sector crece y pasa a ser quien se queda el dinero.",
        "foot"))
    return s


if __name__ == "__main__":
    build(os.path.abspath(OUT),
          "Serie CAGR 30 años  |  Sector 1 de 8  |  Electrificación y red eléctrica",
          story())
    print("written:", os.path.abspath(OUT))
