# SPDX-License-Identifier: GPL-3.0-or-later
"""Unterschiede zwischen Linux, macOS und Windows an einer Stelle."""

import subprocess
import sys
from pathlib import Path

WINDOWS = sys.platform == "win32"
MACOS = sys.platform == "darwin"

PACKAGE_DIR = Path(__file__).parent
# Beim Start aus dem Repo (PYTHONPATH=src) liegen Skripte und Sprung-Host
# neben src/, im installierten Paket unter trmmwebrelay/.
_REPO_DIR = PACKAGE_DIR.parent.parent


def quiet() -> dict:
    """Popen-Argumente: unter Windows kein Konsolenfenster für Hilfsprogramme."""
    if WINDOWS:
        return {"creationflags": subprocess.CREATE_NO_WINDOW}
    return {}


def detached() -> dict:
    """Popen-Argumente für Prozesse, die nicht an Strg+C des Clients hängen sollen."""
    if WINDOWS:
        return {"creationflags": subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP}
    return {"start_new_session": True}


def resource(name: str) -> Path:
    """Pfad zu trmm-scripts/ bzw. jumphost/ (installiert oder im Repo)."""
    for base in (PACKAGE_DIR / "data", _REPO_DIR):
        path = base / name
        if path.exists():
            return path
    raise FileNotFoundError(f"{name} nicht gefunden (Installation unvollständig?)")
