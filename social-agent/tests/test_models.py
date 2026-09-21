from social_agent.models import LIMITS, Draft, Platform


def test_hashtags_se_normalizan_y_deduplican():
    draft = Draft(
        platform=Platform.LINKEDIN,
        topic="x",
        body="y",
        hashtags=["#Inox", " inox2 ", "Inox2", "", "#"],
    )
    assert draft.hashtags == ["Inox", "inox2"]


def test_rendered_concatena_cuerpo_y_hashtags(linkedin_draft):
    rendered = linkedin_draft.rendered()
    assert rendered.startswith("Una barandilla")
    assert rendered.endswith("#AceroInoxidable #Metalisteria")


def test_rendered_sin_hashtags_no_deja_lineas_sueltas():
    draft = Draft(platform=Platform.LINKEDIN, topic="x", body=" hola ", hashtags=[])
    assert draft.rendered() == "hola"


def test_instagram_sin_imagen_es_invalido(instagram_draft):
    instagram_draft.image_url = None
    assert any("requiere una imagen" in e for e in instagram_draft.validation_errors())


def test_linkedin_no_exige_imagen(linkedin_draft):
    assert linkedin_draft.is_valid()


def test_cuerpo_demasiado_largo_se_detecta():
    draft = Draft(
        platform=Platform.LINKEDIN,
        topic="x",
        body="a" * (LIMITS[Platform.LINKEDIN]["body"] + 1),
    )
    assert any("caracteres" in e for e in draft.validation_errors())


def test_exceso_de_hashtags_se_detecta(instagram_draft):
    instagram_draft.hashtags = [f"tag{i}" for i in range(40)]
    assert any("hashtags" in e for e in instagram_draft.validation_errors())
