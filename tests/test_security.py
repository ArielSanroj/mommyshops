import os
import sys
from pathlib import Path

os.environ.setdefault("SKIP_MAIN_IMPORT_FOR_TESTS", "1")

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend-python"
if str(BACKEND_DIR) not in sys.path:
    sys.path.append(str(BACKEND_DIR))

from fastapi import Depends, FastAPI, HTTPException, Header
from fastapi.testclient import TestClient

from security import RateLimiterMiddleware


def build_rate_limited_app(limit: int, window: int = 60) -> FastAPI:
    app = FastAPI()
    app.add_middleware(RateLimiterMiddleware, limit=limit, window_seconds=window)

    @app.get("/debug/simple")
    def debug_simple():
        return {"message": "ok"}

    return app


def build_protected_app() -> FastAPI:
    app = FastAPI()

    async def require_token(authorization: str | None = Header(default=None)):
        if not authorization or not authorization.lower().startswith("bearer "):
            raise HTTPException(status_code=401, detail="Token de autenticación requerido")

    @app.get("/secure", dependencies=[Depends(require_token)])
    def secure_endpoint():
        return {"status": "ok"}

    return app


def test_rate_limiter_blocks_excessive_requests():
    app = build_rate_limited_app(limit=2, window=60)
    client = TestClient(app)

    # First two requests should succeed
    assert client.get("/debug/simple").status_code == 200
    assert client.get("/debug/simple").status_code == 200

    # Third request within the same window must be rejected
    response = client.get("/debug/simple")
    assert response.status_code == 429
    assert response.json()["detail"].startswith("Rate limit excedido")


def test_protected_endpoint_requires_token():
    app = build_protected_app()
    client = TestClient(app)

    response = client.get("/secure")
    assert response.status_code == 401
    assert response.json()["detail"] == "Token de autenticación requerido"
