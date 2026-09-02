"""
Informe mensual de la red comercial.

    python -m sales.report

Sustituye al seguimiento manual "cuánto falta para igualar el año pasado":
ese número se cumple por inercia y esconde el declive.
"""
from __future__ import annotations

from sales.analysis import (
    concentracion,
    proyectar_cierre,
    rolling_12m,
    total_comercial,
    total_plaza,
    total_year,
    ventana_homogenea,
)
from sales.data import COMERCIAL_DOMINANTE, MESES, PLAZAS, VENTAS, meses_cerrados

ANOS_CERRADOS = [2022, 2023, 2024, 2025]
ANO_CURSO = 2026
# Meses de antigüedad por debajo de los cuales un comercial sigue en rampa.
UMBRAL_RAMPA_MESES = 18


def eur(valor: float) -> str:
    return f"{valor:>12,.0f} €".replace(",", ".")


def pct(valor: float | None) -> str:
    return "     n/a" if valor is None else f"{valor:+7.1%}"


def _seccion(titulo: str) -> None:
    print(f"\n{titulo}\n{'-' * len(titulo)}")


def evolucion_anual() -> None:
    _seccion("EVOLUCIÓN ANUAL")
    previo = None
    for year in ANOS_CERRADOS:
        total = total_year(year)
        var = pct(total / previo - 1) if previo else "    base"
        print(f"  {year}  {eur(total)}  {var}")
        previo = total
    acumulado = total_year(ANO_CURSO)
    meses = meses_cerrados(ANO_CURSO)
    print(f"  {ANO_CURSO}  {eur(acumulado)}   ({meses} meses cerrados)")
    print(f"\n  Acumulado {ANOS_CERRADOS[0]}→{ANOS_CERRADOS[-1]}: "
          f"{pct(total_year(ANOS_CERRADOS[-1]) / total_year(ANOS_CERRADOS[0]) - 1)}")


def comparativa_homogenea() -> None:
    v = ventana_homogenea(ANO_CURSO - 1, ANO_CURSO)
    _seccion(f"VENTANA HOMOGÉNEA — {MESES[0].lower()}–{MESES[v.meses - 1].lower()}")
    print(f"  {v.year_base}  {eur(v.total_base)}")
    print(f"  {v.year_actual}  {eur(v.total_actual)}   {pct(v.pct)}")
    print()
    for c in sorted(v.comerciales, key=lambda x: x.delta, reverse=True):
        print(f"  {c.comercial:<14}{eur(c.base)}{eur(c.actual)}  {pct(c.pct)}")


def riesgo_concentracion() -> None:
    _seccion(f"CONCENTRACIÓN EN {COMERCIAL_DOMINANTE}")
    print("  El KPI que mide si el riesgo real baja. Objetivo: que caiga.\n")
    for year in ANOS_CERRADOS + [ANO_CURSO]:
        peso = concentracion(year)
        barra = "#" * round(peso * 50)
        print(f"  {year}  {peso:6.1%}  resto {1 - peso:5.1%}  {barra}")


def plazas_con_relevo() -> None:
    for plaza, comerciales in PLAZAS.items():
        _seccion(f"PLAZA {plaza} — {' → '.join(comerciales)}")
        for year in ANOS_CERRADOS:
            detalle = ", ".join(
                f"{c} {total_comercial(year, c):,.0f}".replace(",", ".")
                for c in comerciales
                if total_comercial(year, c)
            )
            print(f"  {year}  {eur(total_plaza(plaza, year))}   {detalle}")
        meses = meses_cerrados(ANO_CURSO)
        print(f"  {ANO_CURSO}  {eur(total_plaza(plaza, ANO_CURSO))}   ({meses} meses)")
        actual = comerciales[-1]
        print(f"\n  12m móviles de {actual}: {eur(rolling_12m(actual, ANO_CURSO, meses))}")
        print(f"  Referencia (último año completo del anterior, "
              f"{ANOS_CERRADOS[-2]}): {eur(total_plaza(plaza, ANOS_CERRADOS[-2]))}")


def incorporaciones() -> None:
    _seccion(f"COMERCIALES EN RAMPA (<{UMBRAL_RAMPA_MESES} meses)")
    print("  Si el embudo de incorporación no funciona, la concentración no baja.\n")
    veteranos = {c for c in VENTAS[ANOS_CERRADOS[0]] if total_comercial(ANOS_CERRADOS[0], c)}
    for comercial in VENTAS[ANO_CURSO]:
        if comercial in veteranos:
            continue
        historico = sum(total_comercial(y, comercial) for y in ANOS_CERRADOS)
        curso = total_comercial(ANO_CURSO, comercial)
        meses_activos = sum(
            1
            for y in ANOS_CERRADOS + [ANO_CURSO]
            for m in VENTAS[y].get(comercial, [])
            if m
        )
        print(f"  {comercial:<14}{eur(historico)} hist. {eur(curso)} {ANO_CURSO}"
              f"   {meses_activos:>2} meses con facturación")


def proyeccion_cierre() -> None:
    p = proyectar_cierre(ANO_CURSO, ANOS_CERRADOS[1:])
    _seccion(f"PROYECCIÓN DE CIERRE {ANO_CURSO}")
    print(f"  Acumulado {p.meses_cerrados} meses:{eur(p.acumulado)}")
    print(f"  Estimación (mediana):    {eur(p.estimacion)}")
    print(f"  Rango por estacionalidad:{eur(p.rango[0])} –{eur(p.rango[1])}")
    print("\n  Pendiente para igualar cada año:")
    for year, falta in sorted(p.pendiente_para_igualar.items()):
        veredicto = "por debajo de la inercia" if falta < p.estimacion - p.acumulado else "exige crecer"
        print(f"    {year}  {eur(falta)}   {veredicto}")


def main() -> None:
    print("=" * 60)
    print("INFORME DE RED COMERCIAL".center(60))
    print("=" * 60)
    evolucion_anual()
    comparativa_homogenea()
    riesgo_concentracion()
    plazas_con_relevo()
    incorporaciones()
    proyeccion_cierre()
    print()


if __name__ == "__main__":
    main()
