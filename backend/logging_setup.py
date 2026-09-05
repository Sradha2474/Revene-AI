"""Structured logging for Revene."""

from __future__ import annotations

import logging
import sys


def setup_logging(level: str = "INFO") -> logging.Logger:
    root = logging.getLogger()
    if root.handlers:
        root.setLevel(getattr(logging, level, logging.INFO))
        return logging.getLogger("revene")

    # Windows consoles are often cp1252 — avoid UnicodeEncodeError on arrows/₹
    stream = sys.stdout
    try:
        stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    except Exception:
        pass

    handler = logging.StreamHandler(stream)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s %(levelname)s [%(name)s] %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
    )
    root.addHandler(handler)
    root.setLevel(getattr(logging, level, logging.INFO))
    # Quiet noisy libs
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    logging.getLogger("engineio").setLevel(logging.WARNING)
    logging.getLogger("socketio").setLevel(logging.WARNING)
    return logging.getLogger("revene")
