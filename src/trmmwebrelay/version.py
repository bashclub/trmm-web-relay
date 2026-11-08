# SPDX-License-Identifier: GPL-3.0-or-later
"""Installierte Version und Hinweis auf eine neuere Version im Repository.

Der Client fragt höchstens einmal am Tag `update_url` ab (Standard: die
pyproject.toml auf `main`) und merkt sich das Ergebnis im Cache. Fehler beim
Abfragen bleiben still: Der Hinweis ist eine Hilfe, keine Voraussetzung.
"""

import json
import logging
import re
import threading
import time
import urllib.request
from importlib import metadata
from pathlib import Path

from trmmwebrelay.config import CACHE_DIR, Config

log = logging.getLogger(__name__)
CACHE_FILE = CACHE_DIR / "version.json"
MAX_AGE = 24 * 3600
_VERSION_RE = re.compile(r'^version\s*=\s*"([^"]+)"', re.M)
_lock = threading.Lock()


def current() -> str:
    try:
        return metadata.version("trmm-web-relay")
    except metadata.PackageNotFoundError:
        # Aus dem Repo gestartet (PYTHONPATH=src)
        pyproject = Path(__file__).resolve().parents[2] / "pyproject.toml"
        try:
            m = _VERSION_RE.search(pyproject.read_text())
            return m.group(1) if m else "unbekannt"
        except OSError:
            return "unbekannt"


def _key(v: str) -> tuple[int, ...]:
    parts = []
    for p in v.split("."):
        m = re.match(r"\d+", p)
        parts.append(int(m.group()) if m else 0)
    return tuple(parts)


def is_newer(latest: str, installed: str) -> bool:
    if not latest or installed == "unbekannt":
        return False
    return _key(latest) > _key(installed)


def _read_cache(url: str) -> dict | None:
    try:
        data = json.loads(CACHE_FILE.read_text())
    except (OSError, ValueError):
        return None
    if data.get("url") != url or time.time() - data.get("checked", 0) > MAX_AGE:
        return None
    return data


def _fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": f"trmm-web-relay/{current()}"})
    with urllib.request.urlopen(req, timeout=8) as r:
        text = r.read(64 * 1024).decode("utf-8", errors="replace")
    m = _VERSION_RE.search(text)
    if not m:
        raise ValueError("keine Version gefunden")
    return m.group(1)


def latest(cfg: Config, refresh: bool = False) -> str:
    """Neueste Version laut update_url, "" wenn abgeschaltet oder unbekannt."""
    url = cfg.update_url.strip()
    if not url:
        return ""
    with _lock:
        cached = None if refresh else _read_cache(url)
        if cached is not None:
            return cached.get("latest", "")
        try:
            value = _fetch(url)
        except Exception as e:  # noqa: BLE001 - Netz, HTTP, Inhalt: nur loggen
            log.info("Neueste Version nicht abrufbar (%s): %s", url, e)
            value = ""
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        CACHE_FILE.write_text(json.dumps({"url": url, "checked": time.time(), "latest": value}))
        return value


def status(cfg: Config) -> dict:
    """Für Steuerseite und check; liest nur den Cache, fragt nicht ab."""
    installed = current()
    url = cfg.update_url.strip()
    cached = _read_cache(url) if url else None
    newest = cached.get("latest", "") if cached else ""
    return {"current": installed, "latest": newest, "update": is_newer(newest, installed)}


def check_in_background(cfg: Config) -> None:
    """Beim Start und danach einmal am Tag (Thread endet mit dem Client)."""

    def loop() -> None:
        while True:
            latest(cfg)
            time.sleep(MAX_AGE)

    threading.Thread(target=loop, daemon=True, name="version").start()
