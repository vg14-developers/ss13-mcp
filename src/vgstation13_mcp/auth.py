import os

import httpx
from authlib.integrations.starlette_client import OAuth
from fastapi import HTTPException, Request

GITHUB_API = "https://api.github.com"


def get_oauth() -> OAuth:
    oauth = OAuth()
    oauth.register(
        name="github",
        client_id=os.environ["VG_OAUTH_CLIENT_ID"],
        client_secret=os.environ["VG_OAUTH_CLIENT_SECRET"],
        access_token_url="https://github.com/login/oauth/access_token",
        authorize_url="https://github.com/login/oauth/authorize",
        api_base_url=GITHUB_API,
        client_kwargs={"scope": "read:user", "code_challenge_method": "S256"},
    )
    return oauth


async def validate_github_token(token: str) -> dict | None:
    """Validate a GitHub access token by calling /user."""
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.get(
            f"{GITHUB_API}/user",
            headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
        )
        if resp.status_code == 200:
            return resp.json()
        return None


async def require_auth(request: Request) -> dict:
    """FastAPI dependency. Accepts either a session cookie or a bearer token."""
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.removeprefix("Bearer ").strip()
        # Look up dynamically so tests can monkeypatch this module attribute.
        import vgstation13_mcp.auth as _self

        user = await _self.validate_github_token(token)
        if user is None:
            raise HTTPException(
                status_code=401,
                detail="invalid bearer token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user

    user = request.session.get("user")
    if not user:
        raise HTTPException(
            status_code=401,
            detail="not authenticated",
            headers={"WWW-Authenticate": 'Bearer realm="vgstation13"'},
        )
    return user
