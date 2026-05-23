import asyncio
import contextlib

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


@pytest.mark.timeout(10)
async def test_sse_endpoint_authenticated_returns_200(monkeypatch, fixture_snapshot):
    monkeypatch.setenv("VG_OAUTH_CLIENT_ID", "test-client")
    monkeypatch.setenv("VG_OAUTH_CLIENT_SECRET", "test-secret")
    monkeypatch.setenv("VG_OAUTH_REDIRECT_URI", "http://testserver/oauth/callback")
    monkeypatch.setenv("VG_SESSION_SECRET", "test-session-secret")

    async def fake_validate(token: str) -> dict | None:
        return {"login": "octocat"} if token == "good" else None

    monkeypatch.setattr("vgstation13_mcp.auth.validate_github_token", fake_validate)
    app = build_app()
    # MCP's SSE handler is a long-lived ASGI response; both starlette TestClient
    # and httpx.ASGITransport buffer the whole response, so they hang. Drive the
    # ASGI app manually, capture the status and first body chunk, then send
    # http.disconnect so the server-side task can unwind.
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": "/sse",
        "raw_path": b"/sse",
        "query_string": b"",
        "headers": [
            (b"host", b"testserver"),
            (b"authorization", b"Bearer good"),
        ],
        "server": ("testserver", 80),
        "client": ("127.0.0.1", 12345),
        "root_path": "",
    }

    receive_disconnect = asyncio.Event()

    async def receive():
        # First call: signal that the request body is finished. Subsequent calls
        # block until we cancel the task, mirroring an idle SSE GET.
        if not getattr(receive, "_sent_request", False):
            receive._sent_request = True
            return {"type": "http.request", "body": b"", "more_body": False}
        await receive_disconnect.wait()
        return {"type": "http.disconnect"}

    captured: dict = {"status": None, "first_chunk": None}
    chunk_event = asyncio.Event()

    async def send(message):
        if message["type"] == "http.response.start":
            captured["status"] = message["status"]
        elif message["type"] == "http.response.body":
            body = message.get("body", b"")
            if body and captured["first_chunk"] is None:
                captured["first_chunk"] = body
                chunk_event.set()

    task = asyncio.create_task(app(scope, receive, send))
    try:
        # Wait for either the first body chunk or the app to finish on its own.
        done, _ = await asyncio.wait(
            [asyncio.create_task(chunk_event.wait()), task],
            return_when=asyncio.FIRST_COMPLETED,
            timeout=5,
        )
        assert chunk_event.is_set() or task.done(), "SSE handler produced no output"
        assert captured["status"] == 200
    finally:
        receive_disconnect.set()
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError, BaseException):
            await task
