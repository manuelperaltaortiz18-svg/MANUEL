import httpx
import pytest

from social_agent.models import Platform
from social_agent.publishers import (
    InstagramPublisher,
    LinkedInPublisher,
    PublishError,
    build_publishers,
)
from social_agent.settings import Settings

ORG_URN = "urn:li:organization:12345"


def _client(handler):
    return httpx.Client(transport=httpx.MockTransport(handler))


# --- LinkedIn ---


def test_linkedin_urn_invalido_falla_pronto():
    with pytest.raises(ValueError):
        LinkedInPublisher("token", "12345")


def test_linkedin_publica_y_lee_el_id_de_la_cabecera(linkedin_draft):
    def handler(request):
        assert request.url.path == "/rest/posts"
        assert request.headers["Authorization"] == "Bearer token"
        return httpx.Response(201, headers={"x-restli-id": "urn:li:share:999"})

    pub = LinkedInPublisher("token", ORG_URN, client=_client(handler))
    result = pub.publish(linkedin_draft)
    assert result.remote_id == "urn:li:share:999"
    assert "urn:li:share:999" in result.url


def test_linkedin_403_explica_que_falta_community_management(linkedin_draft):
    handler = lambda r: httpx.Response(403, text="ACCESS_DENIED")
    pub = LinkedInPublisher("token", ORG_URN, client=_client(handler))
    with pytest.raises(PublishError, match="Community Management"):
        pub.publish(linkedin_draft)


def test_linkedin_401_no_es_reintentable(linkedin_draft):
    handler = lambda r: httpx.Response(401, text="expired")
    pub = LinkedInPublisher("token", ORG_URN, client=_client(handler))
    with pytest.raises(PublishError) as exc:
        pub.publish(linkedin_draft)
    assert exc.value.retryable is False


def test_linkedin_500_es_reintentable(linkedin_draft):
    handler = lambda r: httpx.Response(503, text="down")
    pub = LinkedInPublisher("token", ORG_URN, client=_client(handler))
    with pytest.raises(PublishError) as exc:
        pub.publish(linkedin_draft)
    assert exc.value.retryable is True


# --- Instagram ---


def test_instagram_flujo_completo(instagram_draft):
    seen = []

    def handler(request):
        path = request.url.path
        seen.append(path)
        if path.endswith("/media"):
            return httpx.Response(200, json={"id": "container-1"})
        if path.endswith("/media_publish"):
            return httpx.Response(200, json={"id": "media-1"})
        if path.endswith("/container-1"):
            return httpx.Response(200, json={"status_code": "FINISHED"})
        if path.endswith("/media-1"):
            return httpx.Response(200, json={"permalink": "https://instagr.am/p/x"})
        raise AssertionError(path)

    pub = InstagramPublisher(
        "token", "acct", client=_client(handler), poll_interval_s=0
    )
    result = pub.publish(instagram_draft)
    assert result.remote_id == "media-1"
    assert result.url == "https://instagr.am/p/x"
    assert any(p.endswith("/media_publish") for p in seen)


def test_instagram_espera_a_que_termine_el_procesado(instagram_draft):
    estados = ["IN_PROGRESS", "IN_PROGRESS", "FINISHED"]

    def handler(request):
        path = request.url.path
        if path.endswith("/media"):
            return httpx.Response(200, json={"id": "c1"})
        if path.endswith("/c1"):
            return httpx.Response(200, json={"status_code": estados.pop(0)})
        if path.endswith("/media_publish"):
            return httpx.Response(200, json={"id": "m1"})
        return httpx.Response(200, json={"permalink": None})

    pub = InstagramPublisher("t", "a", client=_client(handler), poll_interval_s=0)
    assert pub.publish(instagram_draft).remote_id == "m1"
    assert estados == []


def test_instagram_error_de_procesado_de_imagen(instagram_draft):
    def handler(request):
        if request.url.path.endswith("/media"):
            return httpx.Response(200, json={"id": "c1"})
        return httpx.Response(
            200, json={"status_code": "ERROR", "status": "imagen no accesible"}
        )

    pub = InstagramPublisher("t", "a", client=_client(handler), poll_interval_s=0)
    with pytest.raises(PublishError, match="no pudo procesar"):
        pub.publish(instagram_draft)


def test_instagram_sin_imagen_no_llama_a_la_api(instagram_draft):
    instagram_draft.image_url = None

    def handler(request):
        raise AssertionError("no deberia haber llamada de red")

    pub = InstagramPublisher("t", "a", client=_client(handler), poll_interval_s=0)
    with pytest.raises(PublishError, match="requiere una imagen"):
        pub.publish(instagram_draft)


def test_instagram_token_caducado(instagram_draft):
    handler = lambda r: httpx.Response(
        400, json={"error": {"code": 190, "message": "Session expired"}}
    )
    pub = InstagramPublisher("t", "a", client=_client(handler), poll_interval_s=0)
    with pytest.raises(PublishError, match="reautorizar"):
        pub.publish(instagram_draft)


def test_instagram_rate_limit_es_reintentable(instagram_draft):
    handler = lambda r: httpx.Response(
        400, json={"error": {"code": 4, "message": "limit reached"}}
    )
    pub = InstagramPublisher("t", "a", client=_client(handler), poll_interval_s=0)
    with pytest.raises(PublishError) as exc:
        pub.publish(instagram_draft)
    assert exc.value.retryable is True


# --- registry ---


def test_registry_omite_plataformas_sin_credenciales(tmp_path):
    settings = Settings(
        linkedin_access_token="t",
        linkedin_author_urn=ORG_URN,
        instagram_access_token="",
        database_path=tmp_path / "q.db",
    )
    publishers = build_publishers(settings)
    assert Platform.LINKEDIN in publishers
    assert Platform.INSTAGRAM not in publishers


def test_registry_vacio_sin_configuracion(tmp_path):
    assert build_publishers(Settings(database_path=tmp_path / "q.db")) == {}
