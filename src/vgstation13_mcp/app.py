import os

from fastapi import Depends, FastAPI, HTTPException, Request
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

    from mcp.server.sse import SseServerTransport

    from vgstation13_mcp.server import mcp as mcp_server

    sse = SseServerTransport("/messages/")

    @app.get("/sse")
    async def handle_sse(
        request: Request,
        user: dict = Depends(require_auth),  # noqa: B008
    ):
        async with sse.connect_sse(request.scope, request.receive, request._send) as (read, write):
            await mcp_server._mcp_server.run(
                read,
                write,
                mcp_server._mcp_server.create_initialization_options(),
            )

    @app.post("/messages/{session_id}")
    async def handle_messages(
        session_id: str,
        request: Request,
        user: dict = Depends(require_auth),  # noqa: B008
    ):
        await sse.handle_post_message(request.scope, request.receive, request._send)

    from vgstation13_mcp.ratelimit import TokenBucket

    read_bucket = TokenBucket(capacity=600, refill_per_second=10.0)

    @app.middleware("http")
    async def rate_limit(request: Request, call_next):
        user_key = request.headers.get(
            "Authorization", request.client.host if request.client else "anonymous"
        )
        if not read_bucket.take(user_key):
            raise HTTPException(
                status_code=429,
                detail="rate limit exceeded",
                headers={"Retry-After": "60"},
            )
        return await call_next(request)

    return app
