import os

from fastapi import Depends, FastAPI, Request
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

from vgstation13_mcp.auth import get_oauth, require_auth


def build_app() -> FastAPI:
    app = FastAPI(title="vgstation13-mcp")
    app.add_middleware(SessionMiddleware, secret_key=os.environ["VG_SESSION_SECRET"])
    oauth = get_oauth()

    @app.get("/health")
    async def health(user: dict = Depends(require_auth)) -> dict:  # noqa: B008
        return {"status": "ok", "user": user.get("login", "")}

    @app.get("/oauth/authorize")
    async def authorize(request: Request):
        redirect_uri = os.environ["VG_OAUTH_REDIRECT_URI"]
        return await oauth.github.authorize_redirect(request, redirect_uri)

    @app.get("/oauth/callback")
    async def callback(request: Request):
        token = await oauth.github.authorize_access_token(request)
        resp = await oauth.github.get("user", token=token)
        user = resp.json()
        allowed_orgs = os.environ.get("VG_MCP_ALLOWED_ORGS", "").split(",")
        if allowed_orgs and allowed_orgs != [""]:
            orgs_resp = await oauth.github.get("user/orgs", token=token)
            user_orgs = {o["login"] for o in orgs_resp.json()}
            if not user_orgs.intersection(allowed_orgs):
                return {"error": "not a member of an allowed org"}
        request.session["user"] = {"login": user["login"], "id": user["id"]}
        return RedirectResponse("/")

    @app.get("/sse")
    async def sse_placeholder(user: dict = Depends(require_auth)):  # noqa: B008
        return {"placeholder": "sse"}

    return app
