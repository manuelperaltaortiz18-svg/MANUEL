import pytest

from social_agent.brand import load_brand_profile
from social_agent.models import Platform


def test_perfil_de_marca_carga(brand):
    assert brand.nombre
    assert brand.pilares


def test_rotacion_de_pilares_es_ciclica_y_estable(brand):
    n = len(brand.pilares)
    assert brand.pillar_for_week(3) is brand.pillar_for_week(3 + n)
    vistos = {brand.pillar_for_week(w).id for w in range(n)}
    assert len(vistos) == n


def test_hashtags_base_por_plataforma(brand):
    assert brand.base_hashtags(Platform.INSTAGRAM)
    assert brand.base_hashtags(Platform.LINKEDIN)


def test_perfil_inexistente_falla(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_brand_profile(tmp_path / "no-existe.yaml")
