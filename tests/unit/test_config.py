import pytest

pytestmark = pytest.mark.unit

def test_get_auth_data(monkeypatch):
    from app.core import config as cfg

    class Dummy:
        SECRET_KEY = "k"
        ALGORITHM = "HS256"

    monkeypatch.setattr(cfg, "settings", Dummy(), raising=True)
    assert cfg.get_auth_data() == {"secret_key": "k", "algorithm": "HS256"}