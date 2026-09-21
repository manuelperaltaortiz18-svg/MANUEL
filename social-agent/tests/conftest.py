import pytest

from social_agent.brand import load_brand_profile
from social_agent.models import Draft, Platform
from social_agent.settings import REPO_ROOT
from social_agent.store import DraftQueue


@pytest.fixture
def brand():
    return load_brand_profile(REPO_ROOT / "brand.yaml")


@pytest.fixture
def queue(tmp_path):
    with DraftQueue(tmp_path / "queue.db") as q:
        yield q


@pytest.fixture
def linkedin_draft():
    return Draft(
        platform=Platform.LINKEDIN,
        topic="Barandilla inox a medida",
        body="Una barandilla de AISI 316 para exterior.",
        hashtags=["AceroInoxidable", "Metalisteria"],
    )


@pytest.fixture
def instagram_draft():
    return Draft(
        platform=Platform.INSTAGRAM,
        topic="Detalle de soldadura",
        body="Cordon de soldadura TIG pulido a mano.",
        hashtags=["inox", "soldadura"],
        image_url="https://cuperinox.es/media/soldadura.jpg",
    )
