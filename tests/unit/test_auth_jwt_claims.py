import pytest
from jose import jwt

pytestmark = pytest.mark.unit

def test_jwt_contains_claims(monkeypatch):
    from app.auth import utils as auth_utils
    from app.core import config as core_config

    monkeypatch.setattr(core_config, "SECRET_KEY", "test-secret", raising=False)
    if hasattr(core_config, "settings"):
        monkeypatch.setattr(core_config.settings, "SECRET_KEY", "test-secret", raising=False)

    monkeypatch.setattr(auth_utils, "SECRET_KEY", "test-secret", raising=False)
    monkeypatch.setattr(auth_utils, "ALGORITHM", "HS256", raising=False)

    data = {"sub": "1", "is_admin": False}
    token = auth_utils.create_access_token(data)

    decoded = jwt.decode(token, "test-secret", algorithms=["HS256"])
    assert decoded["sub"] == "1"
    assert decoded["is_admin"] is False
    assert "exp" in decoded