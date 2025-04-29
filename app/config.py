from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# Load .env (if present) from project root
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")


@dataclass(frozen=True)
class Settings:  # all immutable
    openai_api_key: str
    openai_org_id: str | None
    model: str
    max_tokens: int
    request_timeout: int


def _make_settings() -> Settings:
    """Pull values from env with sensible fall-backs."""
    return Settings(
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        openai_org_id=os.getenv("OPENAI_ORG_ID"),
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        max_tokens=int(os.getenv("OPENAI_MAX_TOKENS", "4096")),
        request_timeout=int(os.getenv("REQUEST_TIMEOUT", "60")),
    )


settings: Settings = _make_settings()


def ensure_env() -> None:
    """Fail fast if critical secrets are missing."""
    if not settings.openai_api_key:
        raise RuntimeError(
            "OPENAI_API_KEY not set.  "
            "Create a .env file (see .env.example) or export the variable."
        )
