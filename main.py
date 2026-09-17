"""CLI entrypoint. Also exports FastAPI `app` for Vercel."""

from src.webapp import app  # noqa: F401
from src.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
