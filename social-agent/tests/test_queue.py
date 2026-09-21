from social_agent.models import DraftStatus, Platform


def test_alta_y_recuperacion_conserva_los_campos(queue, instagram_draft):
    saved = queue.add(instagram_draft)
    assert saved.id is not None

    loaded = queue.get(saved.id)
    assert loaded.body == instagram_draft.body
    assert loaded.hashtags == instagram_draft.hashtags
    assert loaded.image_url == instagram_draft.image_url
    assert loaded.status is DraftStatus.PENDING


def test_publicar_fija_la_fecha(queue, linkedin_draft):
    d = queue.add(linkedin_draft)
    queue.set_status(d.id, DraftStatus.PUBLISHED, remote_id="urn:li:share:1")
    loaded = queue.get(d.id)
    assert loaded.status is DraftStatus.PUBLISHED
    assert loaded.remote_id == "urn:li:share:1"
    assert loaded.published_at is not None


def test_el_remote_id_no_se_pisa_con_none(queue, linkedin_draft):
    d = queue.add(linkedin_draft)
    queue.set_status(d.id, DraftStatus.PUBLISHED, remote_id="abc")
    queue.set_status(d.id, DraftStatus.FAILED, error="algo")
    assert queue.get(d.id).remote_id == "abc"


def test_filtrado_por_estado_y_plataforma(queue, linkedin_draft, instagram_draft):
    queue.add(linkedin_draft)
    ig = queue.add(instagram_draft)
    queue.set_status(ig.id, DraftStatus.APPROVED)

    assert len(queue.list(status=DraftStatus.PENDING)) == 1
    assert len(queue.list(platform=Platform.INSTAGRAM)) == 1
    assert queue.counts_by_status() == {"pending": 1, "approved": 1}


def test_asociar_imagen_y_editar_cuerpo(queue, linkedin_draft):
    d = queue.add(linkedin_draft)
    queue.set_image(d.id, "https://cuperinox.es/a.jpg")
    queue.update_body(d.id, "texto nuevo")
    loaded = queue.get(d.id)
    assert loaded.image_url == "https://cuperinox.es/a.jpg"
    assert loaded.body == "texto nuevo"


def test_get_de_id_inexistente_devuelve_none(queue):
    assert queue.get(9999) is None
