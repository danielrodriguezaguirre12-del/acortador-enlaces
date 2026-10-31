"""API REST del acortador de enlaces."""
import uuid
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from . import db
from .config import settings
from .schemas import LinkInfo, ShortenRequest, ShortenResponse

app = FastAPI(title="Acortador de enlaces", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)


def _is_valid_uuid(value: str) -> bool:
    try:
        uuid.UUID(value)
        return True
    except ValueError:
        return False


def _find_or_404(short_code: str) -> dict:
    item = db.get_link(short_code) if _is_valid_uuid(short_code) else None
    if item is None:
        raise HTTPException(status_code=404, detail="Enlace no encontrado")
    return item


def _public_base_url(request: Request) -> str:
    return settings.base_url or str(request.base_url).rstrip("/")


@app.get("/health", tags=["sistema"])
def health():
    return {"status": "ok"}


@app.post("/shorten", response_model=ShortenResponse, status_code=201, tags=["enlaces"])
def shorten(payload: ShortenRequest, request: Request):
    """Crea un enlace corto: genera el UUID y lo guarda en DynamoDB."""
    short_code = str(uuid.uuid4())
    original_url = str(payload.original_url)
    created_at = datetime.now(timezone.utc).isoformat()

    db.save_link(short_code, original_url, created_at)

    return ShortenResponse(
        short_code=short_code,
        original_url=original_url,
        short_url=f"{_public_base_url(request)}/{short_code}",
    )


@app.get("/urls/{short_code}", response_model=LinkInfo, tags=["enlaces"])
def link_info(short_code: str):
    """Devuelve la información de un enlace en JSON."""
    return LinkInfo(**_find_or_404(short_code))


@app.get("/{short_code}", status_code=307, tags=["enlaces"])
def redirect(short_code: str):
    """Busca el UUID en DynamoDB y redirige al navegador a la URL original."""
    item = _find_or_404(short_code)
    return RedirectResponse(url=item["original_url"], status_code=307)
