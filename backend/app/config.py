"""Configuración de la aplicación a partir de variables de entorno."""
from __future__ import annotations

import os
from dataclasses import dataclass, field

try:  # En desarrollo local se puede usar un archivo .env
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # En EC2 las variables llegan desde systemd
    pass


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    aws_region: str = field(default_factory=lambda: os.getenv("AWS_REGION", "us-east-1"))
    table_name: str = field(default_factory=lambda: os.getenv("TABLE_NAME", "short_links"))
    # URL pública del backend, p. ej. http://3.85.10.20:8000. Si está vacía,
    # se usa la URL con la que llegó la petición.
    base_url: str = field(default_factory=lambda: os.getenv("BASE_URL", "").rstrip("/"))
    # Orígenes permitidos por CORS (URL del sitio en S3), separados por comas.
    allowed_origins: list[str] = field(
        default_factory=lambda: _split_csv(os.getenv("ALLOWED_ORIGINS", "*"))
    )


settings = Settings()
