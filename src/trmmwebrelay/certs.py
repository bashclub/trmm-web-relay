# SPDX-License-Identifier: GPL-3.0-or-later
"""SSH-CA je Server und kurzlebige Zertifikate je Sitzung.

Der Sprung-Host vertraut nur der CA (TRUSTED_CA). Für jede Anmeldung
erzeugt der Client einen Wegwerf-Schlüssel und signiert ihn für wenige
Minuten: Principal „site-<id>“ für den Agenten, „wr-admin“ für den Client.
Ist die Anmeldung erfolgt, ist das Zertifikat wertlos; der Tunnel läuft
weiter, bis eine Seite ihn beendet.
"""

import getpass
import socket
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from trmmwebrelay import keystore
from trmmwebrelay.config import Server
from trmmwebrelay.platform import quiet


def site_principal(site_id: int) -> str:
    return f"site-{site_id}"


def ca_public(server: Server) -> str | None:
    return keystore.get(server.ca_key_name + ".pub")


def ensure_ca(server: Server) -> tuple[str, bool]:
    """Gibt den öffentlichen CA-Schlüssel zurück und ob er neu angelegt wurde."""
    pub = ca_public(server)
    if pub and keystore.get(server.ca_key_name):
        return pub, False
    comment = f"trmm-web-relay-ca {server.id} {getpass.getuser()}@{socket.gethostname()}"
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "ca"
        subprocess.run(
            ["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-C", comment, "-f", str(path)],
            check=True, capture_output=True, **quiet(),
        )
        keystore.put(server.ca_key_name, path.read_text())
        pub = path.with_suffix(".pub").read_text().strip()
        keystore.put(server.ca_key_name + ".pub", pub)
    return pub, True


@dataclass
class Credential:
    key: str  # privater Schlüssel (OpenSSH-Format)
    cert: str  # Zertifikat (eine Zeile)


def issue(server: Server, principal: str, key_id: str, minutes: int = 15) -> Credential:
    """Wegwerf-Schlüssel mit Zertifikat, gültig von -5 bis +<minutes> Minuten."""
    ca = keystore.require(server.ca_key_name, f"CA für {server.name}")
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        ca_path = d / "ca"
        ca_path.touch(mode=0o600)
        ca_path.write_text(ca.rstrip("\n") + "\n")
        key_path = d / "key"
        run = dict(check=True, capture_output=True, **quiet())
        subprocess.run(
            ["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-C", key_id, "-f", str(key_path)], **run
        )
        subprocess.run(
            [
                "ssh-keygen", "-q", "-s", str(ca_path), "-I", key_id, "-n", principal,
                "-V", f"-5m:+{minutes}m", "-O", "clear", "-O", "permit-port-forwarding",
                str(key_path) + ".pub",
            ],
            **run,
        )
        return Credential(
            key=key_path.read_text(),
            cert=(d / "key-cert.pub").read_text().strip(),
        )


def write_credential(cred: Credential, directory: Path) -> tuple[Path, Path]:
    """Legt Schlüssel und Zertifikat für ssh ab (nur für den Benutzer lesbar)."""
    key = directory / "key"
    cert = directory / "key-cert.pub"
    key.touch(mode=0o600)
    key.write_text(cred.key)
    cert.write_text(cred.cert + "\n")
    return key, cert


def fingerprint(pubkey_line: str) -> str:
    r = subprocess.run(
        ["ssh-keygen", "-lf", "-"], input=pubkey_line, capture_output=True, text=True,
        check=False, **quiet(),
    )
    return r.stdout.strip()
