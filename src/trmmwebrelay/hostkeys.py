# SPDX-License-Identifier: GPL-3.0-or-later
"""Host-Schlüssel der Sprung-Hosts: einmal abrufen, bestätigen, eigene known_hosts.

Der Client nutzt eine eigene Datei statt ~/.ssh/known_hosts und gibt die
Zeilen an die Agenten weiter (StrictHostKeyChecking=yes auf beiden Seiten).
"""

import subprocess

from trmmwebrelay.config import STATE_DIR
from trmmwebrelay.platform import quiet

KNOWN_HOSTS = STATE_DIR / "known_hosts"


def host_name(host: str, port: int) -> str:
    return host if port == 22 else f"[{host}]:{port}"


def scan(host: str, port: int) -> list[str]:
    """Fragt die Host-Schlüssel ab (noch ungeprüft, erst nach Bestätigung speichern)."""
    r = subprocess.run(
        ["ssh-keyscan", "-4", "-T", "10", "-t", "ed25519,ecdsa,rsa", "-p", str(port), host],
        capture_output=True, text=True, check=False, timeout=30, **quiet(),
    )
    lines = [l for l in r.stdout.splitlines() if l and not l.startswith("#")]
    if not lines:
        err = r.stderr.strip().splitlines()
        raise RuntimeError(
            f"Sprung-Host {host}:{port} nicht erreichbar" + (f": {err[-1]}" if err else "")
        )
    return lines


def fingerprints(lines: list[str]) -> list[str]:
    """SHA256-Fingerabdrücke in der Form „ED25519 SHA256:…“."""
    out = []
    for line in lines:
        parts = line.split()
        if len(parts) < 3:
            continue
        r = subprocess.run(
            ["ssh-keygen", "-lf", "-"], input=f"{parts[1]} {parts[2]}\n",
            capture_output=True, text=True, check=False, **quiet(),
        )
        f = r.stdout.split()
        if len(f) >= 2:
            out.append(f"{f[-1].strip('()')} {f[1]}")
    return out


def stored(host: str, port: int) -> list[str]:
    name = host_name(host, port)
    if not KNOWN_HOSTS.exists():
        return []
    return [l for l in KNOWN_HOSTS.read_text().splitlines() if l.split(" ", 1)[0] == name]


def store(host: str, port: int, lines: list[str]) -> None:
    name = host_name(host, port)
    keep = []
    if KNOWN_HOSTS.exists():
        keep = [l for l in KNOWN_HOSTS.read_text().splitlines() if l.split(" ", 1)[0] != name]
    new = [l for l in lines if l.split(" ", 1)[0] == name]
    if not new:
        raise ValueError("Keine passenden Host-Schlüssel")
    KNOWN_HOSTS.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    tmp = KNOWN_HOSTS.with_suffix(".tmp")
    tmp.write_text("\n".join(keep + new) + "\n")
    tmp.replace(KNOWN_HOSTS)


def require(host: str, port: int) -> str:
    lines = stored(host, port)
    if not lines:
        raise RuntimeError(
            f"Host-Schlüssel von {host}:{port} noch nicht bestätigt (Einrichtung im Client)"
        )
    return "\n".join(lines) + "\n"
