import pytest
from fastapi.testclient import TestClient

from vgstation13_mcp.app import build_app


@pytest.fixture
def client(monkeypatch, fixture_snapshot):
    monkeypatch.setenv("VG_OAUTH_CLIENT_ID", "test-client")
    monkeypatch.setenv("VG_OAUTH_CLIENT_SECRET", "test-secret")
    monkeypatch.setenv("VG_OAUTH_REDIRECT_URI", "http://testserver/oauth/callback")
    monkeypatch.setenv("VG_SESSION_SECRET", "test-session-secret")
    app = build_app()
    return TestClient(app)


def test_unauthenticated_request_returns_401(client):
    resp = client.get("/sse")
    assert resp.status_code == 401
    assert "Bearer" in resp.headers.get("WWW-Authenticate", "")


def test_authorize_redirects_to_github(client):
    resp = client.get("/oauth/authorize", follow_redirects=False)
    # authlib's authorize_redirect returns a 302 (Found) by default.
    assert resp.status_code in (302, 307)
    assert resp.headers["location"].startswith("https://github.com/login/oauth/authorize")
    assert "client_id=test-client" in resp.headers["location"]
    assert "code_challenge" in resp.headers["location"]
    assert "code_challenge_method=S256" in resp.headers["location"]


def test_bearer_token_path_accepts_valid_github_token(client, monkeypatch):
    async def fake_validate(token: str) -> dict | None:
        if token == "valid-token":
            return {"login": "octocat"}
        return None

    monkeypatch.setattr("vgstation13_mcp.auth.validate_github_token", fake_validate)
    resp = client.get("/health", headers={"Authorization": "Bearer valid-token"})
    assert resp.status_code == 200


def test_bearer_token_path_rejects_invalid(client, monkeypatch):
    async def fake_validate(token: str) -> dict | None:
        return None

    monkeypatch.setattr("vgstation13_mcp.auth.validate_github_token", fake_validate)
    resp = client.get("/sse", headers={"Authorization": "Bearer bad-token"})
    assert resp.status_code == 401
