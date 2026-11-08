# SPDX-License-Identifier: GPL-3.0-or-later
"""Geheimnisse: Schlüsselbund des Systems, sonst ein Ordner nur für diesen Benutzer.

Ohne nutzbaren Schlüsselbund (z. B. Server ohne Desktop, Entwicklung) liegen
sie als Dateien mit Rechten 0600 in TRMM_WEB_RELAY_SECRETS_DIR, Standard
~/.local/share/trmm-web-relay/secrets.

Werte werden nie ausgegeben oder geloggt.
"""

import os
from pathlib import Path

SERVICE = "trmm-web-relay"
DEV_DIR = Path(
    os.environ.get("TRMM_WEB_RELAY_SECRETS_DIR", "~/.local/share/trmm-web-relay/secrets")
).expanduser()

try:
    import keyring  # optional
except ImportError:  # pragma: no cover
    keyring = None


def get(name: str) -> str | None:
    if keyring is not None:
        try:
            value = keyring.get_password(SERVICE, name)
            if value:
                return value
        except Exception:
            pass
    path = DEV_DIR / name
    if path.exists():
        return path.read_text().strip()
    return None


def put(name: str, value: str) -> str:
    """Speichert ein Geheimnis und gibt den Ablageort zurück."""
    if keyring is not None:
        try:
            keyring.set_password(SERVICE, name, value)
            return f"Schlüsselbund ({SERVICE}/{name})"
        except Exception:
            pass
    DEV_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
    path = DEV_DIR / name
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as fh:
        fh.write(value.rstrip("\n") + "\n")
    return str(path)


def delete(name: str) -> None:
    if keyring is not None:
        try:
            keyring.delete_password(SERVICE, name)
        except Exception:
            pass
    (DEV_DIR / name).unlink(missing_ok=True)


def require(name: str, what: str) -> str:
    value = get(name)
    if not value:
        raise RuntimeError(f"{what} fehlt (Einrichtung im Client öffnen)")
    return value
