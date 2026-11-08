# SPDX-License-Identifier: GPL-3.0-or-later
"""Server-Installer als eine Datei: Image-Quellen und install.sh, Werte vorausgefüllt.

Der Client erzeugt ihn in der Einrichtung. Er enthält nur öffentliche Daten
(TRMM-Adresse, öffentlicher CA-Schlüssel); den TRMM-Key fragt install.sh
auf dem Server ab.
"""

import base64
import datetime
import getpass
import io
import re
import socket
import tarfile

from trmmwebrelay import certs
from trmmwebrelay.config import Server
from trmmwebrelay.platform import resource

FILES = ["Containerfile", "sshd_config", "entrypoint.sh", "refresh-allowed.sh", "principals.sh", "install.sh"]


def _safe(value: str) -> str:
    """Nur Zeichen, die in "${VAR:=…}" nichts auslösen."""
    if not re.fullmatch(r"[A-Za-z0-9+/=:._@ -]*", value):
        raise ValueError(f"Unerwartete Zeichen in {value!r}")
    return value


def filename(server: Server) -> str:
    return f"trmm-web-relay-sprunghost-{server.id}.sh"


def build(server: Server) -> str:
    ca = certs.ca_public(server)
    if not ca:
        raise RuntimeError("Erst die CA erzeugen")
    src = resource("jumphost")
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for name in FILES:
            info = tar.gettarinfo(str(src / name), arcname=name)
            info.uid = info.gid = 0
            info.uname = info.gname = ""
            info.mode = 0o755 if name.endswith(".sh") else 0o644
            with open(src / name, "rb") as fh:
                tar.addfile(info, fh)
    payload = base64.encodebytes(buf.getvalue()).decode()
    made = f"{getpass.getuser()}@{socket.gethostname()}, {datetime.date.today().isoformat()}"
    return f"""#!/usr/bin/env bash
# TRMM Web-Relay: Sprung-Host für „{server.name}“ installieren oder aktualisieren.
# Erzeugt von {made}. Enthält nur öffentliche Daten.
#
# Auf dem Server (Linux mit Podman ab 4.4) als root oder Dienstbenutzer:
#   bash {filename(server)}
# Fragt den TRMM-Key nur zum Lesen ab (Rechte: List Clients, List Agents).
# Weitere Werte und Optionen: bash {filename(server)} --help

set -euo pipefail
: "${{TRMM_URL:={_safe(server.trmm_url)}}}"
: "${{TRUSTED_CA:={_safe(ca)}}}"
: "${{PUBLIC_PORT:={server.jump_port}}}"
export TRMM_URL TRUSTED_CA PUBLIC_PORT
dir=$(mktemp -d)
trap 'rm -rf "$dir"' EXIT
sed '1,/^__ARCHIV__$/d' "$0" | base64 -d | tar -xz -C "$dir"
bash "$dir/install.sh" "$@"
exit 0
__ARCHIV__
{payload}"""
