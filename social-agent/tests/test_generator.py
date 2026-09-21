import json

import pytest

from social_agent.content.generator import GenerationError, _parse_json
from social_agent.content import ContentGenerator
from social_agent.models import LIMITS, Platform
from social_agent.settings import Settings


class _Block:
    type = "text"

    def __init__(self, text):
        self.text = text


class _Response:
    def __init__(self, text):
        self.content = [_Block(text)]


class FakeMessages:
    def __init__(self, replies):
        self._replies = list(replies)
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return _Response(self._replies.pop(0))


class FakeClient:
    def __init__(self, replies):
        self.messages = FakeMessages(replies)


def _payload(body="Cuerpo de prueba.", tags=None):
    return json.dumps(
        {
            "topic": "Tema de prueba",
            "body": body,
            "hashtags": tags if tags is not None else ["inox", "metalisteria"],
            "image_brief": "Detalle de una pieza pulida",
        }
    )


@pytest.fixture
def settings(tmp_path):
    return Settings(anthropic_api_key="test-key", database_path=tmp_path / "q.db")


def test_genera_borrador_valido(settings, brand):
    client = FakeClient([_payload()])
    gen = ContentGenerator(settings, brand, client=client)
    draft = gen.generate(Platform.LINKEDIN, week=1)

    assert draft.platform is Platform.LINKEDIN
    assert draft.body == "Cuerpo de prueba."
    assert draft.is_valid()
    # El image_brief se conserva como nota para el revisor.
    assert "pulida" in draft.error


def test_json_envuelto_en_bloque_de_codigo(settings, brand):
    client = FakeClient(["```json\n" + _payload() + "\n```"])
    gen = ContentGenerator(settings, brand, client=client)
    assert gen.generate(Platform.INSTAGRAM, week=2).body == "Cuerpo de prueba."


def test_reintenta_cuando_el_modelo_se_pasa_de_largo(settings, brand):
    demasiado = "a" * (LIMITS[Platform.LINKEDIN]["body"] + 50)
    client = FakeClient([_payload(body=demasiado), _payload()])
    gen = ContentGenerator(settings, brand, client=client)

    draft = gen.generate(Platform.LINKEDIN, week=1)
    assert draft.is_valid()
    assert len(client.messages.calls) == 2


def test_instagram_sin_imagen_no_bloquea_la_generacion(settings, brand):
    # La imagen la adjunta el revisor humano despues, no el generador.
    client = FakeClient([_payload()])
    gen = ContentGenerator(settings, brand, client=client)
    draft = gen.generate(Platform.INSTAGRAM, week=1)
    assert draft.image_url is None


def test_falla_tras_agotar_los_reintentos(settings, brand):
    client = FakeClient(["no soy json"] * 3)
    gen = ContentGenerator(settings, brand, client=client)
    with pytest.raises(GenerationError):
        gen.generate(Platform.LINKEDIN, week=1)


def test_sin_api_key_falla_al_construir(brand, tmp_path):
    with pytest.raises(RuntimeError):
        ContentGenerator(
            Settings(anthropic_api_key="", database_path=tmp_path / "q.db"),
            brand,
            client=FakeClient([]),
        )


def test_parse_json_rechaza_texto_sin_objeto():
    with pytest.raises(ValueError):
        _parse_json("no hay json aqui")
