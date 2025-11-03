import pytest

pytestmark = pytest.mark.unit

def test_hash_and_verify_password():
    from app.auth.utils import get_password_hash, verify_password
    h = get_password_hash("secret")
    assert verify_password("secret", h)
    assert not verify_password("wrong", h)

def test_create_access_token_structure():
    from app.auth.utils import create_access_token
    tok = create_access_token({"sub": "1", "is_admin": False})
    assert isinstance(tok, str) and "." in tok