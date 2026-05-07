from __future__ import annotations

import os


def _bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


class Config:
    DATABASE_URL: str = os.environ.get(
        "DATABASE_URL",
        "postgresql://rimbot:rimbot@localhost:5432/rimbot",
    )
    CORS_ORIGINS: list[str] = [
        origin.strip()
        for origin in os.environ.get("CORS_ORIGINS", "*").split(",")
        if origin.strip()
    ] or ["*"]
    DEBUG: bool = _bool(os.environ.get("FLASK_DEBUG"), False)
    TESTING: bool = False
