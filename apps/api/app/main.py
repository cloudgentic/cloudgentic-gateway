import secrets
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.request_context import set_client_ip

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup — warm up Firebase SDK in cloud mode
    if settings.deployment_mode == "cloud":
        try:
            from cloud.auth.firebase_adapter import _get_firebase_app

            _get_firebase_app()
        except Exception as e:
            import logging

            logging.getLogger(__name__).warning(f"Firebase init deferred: {e}")
    yield
    # Shutdown


app = FastAPI(
    title="CloudGentic Gateway",
    description="Secure AI agent account gateway",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    """Capture client IP into context var for audit logging."""
    client_ip = None
    if request.client:
        client_ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip() or request.client.host
    set_client_ip(client_ip)
    response = await call_next(request)
    return response


@app.middleware("http")
async def security_headers(request: Request, call_next):
    # Per-request nonce so the landing page can run its inline WebGL script
    # without resorting to 'unsafe-inline'. Set before call_next so the route
    # handler can read it off request.state and stamp it on the <script> tag.
    nonce = secrets.token_urlsafe(16)
    request.state.csp_nonce = nonce

    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    # Landing page needs inline styles + Google Fonts; API routes use strict CSP
    if request.url.path == "/":
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            f"script-src 'self' 'nonce-{nonce}'; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data:; "
            "connect-src 'self'"
        )
    else:
        response.headers["Content-Security-Policy"] = "default-src 'self'; connect-src 'self' http://localhost:*"
    return response


# Include API routes
app.include_router(api_router)

# MCP server is available as a standalone process via:
# python -m app.mcp.server
# Or via: fastmcp run app.mcp.server:mcp


@app.get("/")
async def root(request: Request):
    if settings.deployment_mode == "cloud":
        try:
            from cloud.landing import get_landing_html
            from fastapi.responses import HTMLResponse

            nonce = getattr(request.state, "csp_nonce", "")
            # TypeError guards against an older cloud image whose
            # get_landing_html() predates the nonce parameter.
            return HTMLResponse(content=get_landing_html(nonce=nonce))
        except (ImportError, TypeError):
            pass
    return {
        "service": "CloudGentic Gateway",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/api/v1/health",
    }
