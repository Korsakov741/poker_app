import base64
import os
import secrets
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware

from .routes import equity, ranges, players, hands, session, decision

app = FastAPI(title="Motor de decisión de póker")


class BasicAuthMiddleware(BaseHTTPMiddleware):
    """
    Protege TODA la app (frontend + API) con usuario/clave simple —
    el navegador pide las credenciales con su propio cartel nativo,
    no hace falta ninguna pantalla de login propia. Usuario y clave
    salen de variables de entorno (APP_USERNAME / APP_PASSWORD) para
    no dejar la contraseña escrita en el código — se configuran en el
    panel de Render (o en tu compu si corrés local), nunca se suben
    al repositorio.
    """

    async def dispatch(self, request: Request, call_next):
        username = os.environ.get("APP_USERNAME", "hero")
        password = os.environ.get("APP_PASSWORD", "cambiame")

        auth = request.headers.get("Authorization")
        if auth:
            try:
                scheme, raw = auth.split(" ", 1)
                if scheme.lower() == "basic":
                    decoded = base64.b64decode(raw).decode("utf-8")
                    user, _, pwd = decoded.partition(":")
                    if secrets.compare_digest(user, username) and secrets.compare_digest(pwd, password):
                        return await call_next(request)
            except Exception:
                pass

        return Response(status_code=401, headers={"WWW-Authenticate": 'Basic realm="Acceso protegido"'})


app.add_middleware(BasicAuthMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ya protegido por la clave arriba
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(equity.router)
app.include_router(ranges.router)
app.include_router(players.router)
app.include_router(hands.router)
app.include_router(session.router)
app.include_router(decision.router)

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
