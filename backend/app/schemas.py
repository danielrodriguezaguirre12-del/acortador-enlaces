"""Modelos de entrada y salida de la API."""
from pydantic import AnyHttpUrl, BaseModel


class ShortenRequest(BaseModel):
    original_url: AnyHttpUrl


class ShortenResponse(BaseModel):
    short_code: str
    original_url: str
    short_url: str


class LinkInfo(BaseModel):
    short_code: str
    original_url: str
    created_at: str
