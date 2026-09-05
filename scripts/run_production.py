#!/usr/bin/env python3
"""
Production entrypoint for Revene.

Usage (from repo root):
  python scripts/run_production.py

Requires Razorpay keys + webhook secret (APP_ENV forced to production).
Uses Socket.IO threading mode (no deprecated eventlet).
"""

from __future__ import annotations

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
os.chdir(ROOT)
sys.path.insert(0, os.path.join(ROOT, "backend"))
sys.path.insert(0, os.path.join(ROOT, "engine"))
sys.path.insert(0, os.path.join(ROOT, "monitor"))

from dotenv import load_dotenv

load_dotenv(os.path.join(ROOT, ".env"))
# This script always boots production guards (keys + webhook secret required)
os.environ["APP_ENV"] = "production"
# Keep judge live demo on unless user explicitly disables it
os.environ.setdefault("ENABLE_LIVE_SIMULATOR", "1")

import app as revene_app  # noqa: E402

revene_app.start_background_jobs()
settings = revene_app.SETTINGS
revene_app.log.info(
    "Production boot http://%s:%s simulator=%s open /demo",
    "127.0.0.1" if settings.host in ("0.0.0.0", "::") else settings.host,
    settings.port,
    settings.enable_live_simulator,
)
# threading async_mode (set in app.py) — works on Windows without eventlet
revene_app.socketio.run(
    revene_app.app,
    host=settings.host,
    port=settings.port,
    debug=False,
    allow_unsafe_werkzeug=True,
)
