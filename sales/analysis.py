"""
Métricas de la red comercial.

El criterio de fondo: comparar siempre ventanas homogéneas (mismos meses de
cada año) y separar crecimiento real de traspaso de cartera. Un total anual
contra un año en curso no dice nada.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from sales.data import (
    ANOS_POTENCIAL_PLAZA,
    COMERCIAL_DOMINANTE,
    PLAZAS,
    VENTAS,
    meses_cerrados,
)


def total_year(year: int, hasta_mes: int | None = None) -> float:
    """Facturación total de un año, opcionalmente sólo los primeros `hasta_mes` meses."""
    return sum(total_comercial(year, c, hasta_mes) for c in VENTAS[year])


def total_comercial(year: int, comercial: str, hasta_mes: int | None = None) -> float:
    """Facturación de un comercial en un año. Devuelve 0.0 si no estaba de alta."""
    meses = VENTAS[year].get(comercial, [])
    return float(sum(meses[:hasta_mes] if hasta_mes else meses))


@dataclass
class VariacionComercial:
    """Comparativa de un comercial entre dos años sobre la misma ventana de meses."""
    comercial: str
    base: float
    actual: float

    @property
    def delta(self) -> float:
        return self.actual - self.base

    @property
    def pct(self) -> float | None:
        """None cuando no hay base contra la que comparar (alta nueva)."""
        return (self.actual / self.base - 1) if self.base else None


@dataclass
class VentanaHomogenea:
    """Comparativa entre dos años usando sólo los meses cerrados del más reciente."""
    year_base: int
    year_actual: int
    meses: int
    total_base: float
    total_actual: float
    comerciales: list[VariacionComercial] = field(default_factory=list)

    @property
    def pct(self) -> float | None:
        return (self.total_actual / self.total_base - 1) if self.total_base else None


def ventana_homogenea(year_base: int, year_actual: int) -> VentanaHomogenea:
    """Compara dos años sobre los meses cerrados del año más reciente."""
    meses = min(meses_cerrados(year_base), meses_cerrados(year_actual))
    nombres = sorted(set(VENTAS[year_base]) | set(VENTAS[year_actual]))
    comerciales = [
        VariacionComercial(
            comercial=c,
            base=total_comercial(year_base, c, meses),
            actual=total_comercial(year_actual, c, meses),
        )
        for c in nombres
    ]
    return VentanaHomogenea(
        year_base=year_base,
        year_actual=year_actual,
        meses=meses,
        total_base=total_year(year_base, meses),
        total_actual=total_year(year_actual, meses),
        comerciales=[c for c in comerciales if c.base or c.actual],
    )


def peso_estacional(year: int, desde_mes: int) -> float:
    """Fracción del año que aportan los meses a partir de `desde_mes` (1-indexado)."""
    total = total_year(year)
    if not total:
        return 0.0
    return (total - total_year(year, desde_mes - 1)) / total


@dataclass
class Proyeccion:
    """Cierre estimado de un año en curso, extrapolado por estacionalidad."""
    year: int
    meses_cerrados: int
    acumulado: float
    estimacion: float
    rango: tuple[float, float]
    pendiente_para_igualar: dict[int, float]


def proyectar_cierre(year: int, years_referencia: list[int]) -> Proyeccion:
    """
    Proyecta el cierre de `year` aplicando el peso estacional de cada año de
    referencia. La estimación central es la mediana de las proyecciones.
    """
    meses = meses_cerrados(year)
    acumulado = total_year(year)
    proyecciones = []
    for ref in years_referencia:
        resto = peso_estacional(ref, meses + 1)
        if resto < 1:
            proyecciones.append(acumulado / (1 - resto))
    proyecciones.sort()
    mid = len(proyecciones) // 2
    estimacion = (
        proyecciones[mid]
        if len(proyecciones) % 2
        else (proyecciones[mid - 1] + proyecciones[mid]) / 2
    )
    return Proyeccion(
        year=year,
        meses_cerrados=meses,
        acumulado=acumulado,
        estimacion=estimacion,
        rango=(proyecciones[0], proyecciones[-1]),
        pendiente_para_igualar={r: total_year(r) - acumulado for r in years_referencia},
    )


def concentracion(year: int, comercial: str = COMERCIAL_DOMINANTE) -> float:
    """Peso de un comercial sobre el total del año. El KPI de riesgo real."""
    total = total_year(year)
    return total_comercial(year, comercial) / total if total else 0.0


def total_plaza(plaza: str, year: int, hasta_mes: int | None = None) -> float:
    """Facturación de una plaza sumando a todos los comerciales que la han llevado."""
    return sum(total_comercial(year, c, hasta_mes) for c in PLAZAS[plaza])


def rolling_12m(comercial: str, year_fin: int, mes_fin: int) -> float:
    """
    Facturación de los 12 meses que terminan en (year_fin, mes_fin).

    Neutraliza la estacionalidad: es la única forma honesta de juzgar a un
    comercial que arrancó a mitad de año.
    """
    total = total_comercial(year_fin, comercial, mes_fin)
    restantes = 12 - mes_fin
    if restantes:
        meses = VENTAS.get(year_fin - 1, {}).get(comercial, [])
        total += float(sum(meses[mes_fin:mes_fin + restantes]))
    return total


def potencial_plaza(plaza: str) -> float:
    """
    Facturación de referencia de una plaza: media de los años previos al
    deterioro del comercial saliente. Es el listón correcto para su sucesor —
    el último año del que se iba ya venía tocado por la desconexión.
    """
    years = ANOS_POTENCIAL_PLAZA[plaza]
    return sum(total_plaza(plaza, y) for y in years) / len(years)


def recorrido_plaza(plaza: str, year_fin: int, mes_fin: int) -> float:
    """Diferencia entre el potencial de la plaza y los 12m móviles de su comercial actual."""
    return potencial_plaza(plaza) - rolling_12m(PLAZAS[plaza][-1], year_fin, mes_fin)
