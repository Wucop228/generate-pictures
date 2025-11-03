import uuid

import pytest

pytestmark = pytest.mark.unit

def test_request_id_header_generated(client):
    r = client.post("/auth/logout")
    rid = r.headers.get("X-Request-ID")
    assert rid
    uuid.UUID(rid)

def test_request_id_header_echo(client):
    given = "test-req-id-123"
    r = client.post("/auth/logout", headers={"X-Request-ID": given})
    assert r.headers.get("X-Request-ID") == given