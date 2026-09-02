"""Tests del análisis de red comercial."""
from sales.analysis import (
    concentracion,
    peso_estacional,
    proyectar_cierre,
    rolling_12m,
    total_comercial,
    total_plaza,
    total_year,
    ventana_homogenea,
)
from sales.data import VENTAS, meses_cerrados


def test_totales_anuales_cuadran_con_la_hoja():
    esperado = {2022: 1232957, 2023: 989486, 2024: 936697, 2025: 860313, 2026: 582883}
    for year, total in esperado.items():
        assert total_year(year) == total


def test_meses_cerrados():
    assert meses_cerrados(2025) == 12
    assert meses_cerrados(2026) == 8


def test_total_comercial_recorta_meses():
    assert total_comercial(2026, "ESPIN", 1) == 44979
    assert total_comercial(2026, "ESPIN") == 235179


def test_comercial_no_dado_de_alta_no_rompe():
    assert total_comercial(2022, "MANUEL") == 0.0
    assert total_comercial(2026, "ANGEL") == 0.0


def test_ventana_homogenea_usa_solo_meses_cerrados():
    v = ventana_homogenea(2025, 2026)
    assert v.meses == 8
    assert v.total_base == 565075
    assert v.total_actual == 582883
    assert abs(v.pct - 0.0315) < 0.001


def test_ventana_homogenea_marca_baja_y_alta():
    v = ventana_homogenea(2025, 2026)
    por_nombre = {c.comercial: c for c in v.comerciales}
    assert por_nombre["ANGEL"].pct == -1.0
    assert por_nombre["JUAN ANTONIO"].pct is None  # alta nueva, sin base


def test_peso_estacional_del_ultimo_cuatrimestre():
    # sep-dic pesa entre un tercio y algo más en los años completos recientes.
    for year in (2023, 2024, 2025):
        assert 0.30 < peso_estacional(year, 9) < 0.37


def test_proyeccion_cierre_supera_el_ano_anterior():
    p = proyectar_cierre(2026, [2023, 2024, 2025])
    assert p.acumulado == 582883
    assert p.rango[0] <= p.estimacion <= p.rango[1]
    # El objetivo "igualar 2025" queda por debajo de la propia inercia.
    assert p.pendiente_para_igualar[2025] == 277430
    assert p.estimacion > total_year(2025)


def test_concentracion_no_ha_bajado_en_cuatro_anos():
    assert abs(concentracion(2022) - 0.432) < 0.002
    assert abs(concentracion(2025) - 0.448) < 0.002


def test_total_plaza_suma_el_relevo():
    assert total_plaza("MADRID", 2024) == 123059
    assert total_plaza("MADRID", 2025) == 35146 + 66012


def test_rolling_12m_cruza_el_cambio_de_ano():
    # sep-dic 2025 + ene-ago 2026
    assert rolling_12m("MANUEL", 2026, 8) == 108510


def test_rolling_12m_ano_completo_equivale_al_total():
    assert rolling_12m("ESPIN", 2025, 12) == total_year(2025) * concentracion(2025)


def test_ningun_mes_negativo():
    for year, comerciales in VENTAS.items():
        for comercial, meses in comerciales.items():
            assert all(m >= 0 for m in meses), f"{year} {comercial}"


def test_potencial_plaza_ignora_el_ano_de_desconexion():
    from sales.analysis import potencial_plaza, recorrido_plaza

    # 2024 (123.059 €) no marca el techo: ANGEL ya venía desconectando.
    assert potencial_plaza("MADRID") == (169281 + 168439) / 2
    assert round(recorrido_plaza("MADRID", 2026, 8)) == 60350
