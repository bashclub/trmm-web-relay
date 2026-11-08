# SPDX-License-Identifier: GPL-3.0-or-later
"""Einrichtung eines Servers: prüfen, was fehlt, und es auf Knopfdruck erledigen.

Schreibende Aktionen in TRMM (Felder, Skripte) laufen nur, wenn sie in der
Oberfläche ausdrücklich ausgelöst werden.
"""

import getpass
import socket
import subprocess
import tempfile
from dataclasses import asdict, dataclass, field
from pathlib import Path

from trmmwebrelay import certs, hostkeys
from trmmwebrelay.config import ADMIN_USER, Server
from trmmwebrelay.platform import quiet, resource
from trmmwebrelay.servers import Backend
from trmmwebrelay.trmm import TrmmError

SCRIPTS = {
    "start": ("tunnel-start.sh", "Baut den Tunnel zum Sprung-Host auf (TRMM Web-Relay)."),
    "stop": ("tunnel-stop.sh", "Beendet einen Tunnel von TRMM Web-Relay."),
}

# Rechte der TRMM-Rolle, die zu den Endpunkten gehören
READ_CHECKS = [
    ("/clients/", "List Clients"),
    ("/agents/?detail=false", "List Agents"),
    ("/core/customfields/", "View Custom Fields"),
    ("/scripts/", "List Scripts"),
]

# Schreibrechte, geprüft mit einer Kennung, die es nicht gibt (403 = fehlt, 404 = erlaubt)
WRITE_CHECKS = [
    ("PUT", "/clients/sites/999999999/", "Manage Sites"),
    ("PUT", "/scripts/999999999/", "Manage Scripts"),
    ("PUT", "/core/customfields/999999999/", "Manage Custom Fields"),
]
WRITE_USES = {
    "Manage Sites": "Ziele und Tunnel-Agenten in der Steuerseite bearbeiten",
    "Manage Scripts": "Skripte aus der Einrichtung anlegen/aktualisieren",
    "Manage Custom Fields": "Felder aus der Einrichtung anlegen",
}


@dataclass
class Item:
    id: str
    title: str
    state: str  # ok, fehlt, fehler, info
    detail: str = ""
    action: str = ""  # Kennung für /api/setup/action
    action_label: str = ""
    writes_trmm: bool = False
    data: dict = field(default_factory=dict)


def script_body(kind: str) -> str:
    return (resource("trmm-scripts") / SCRIPTS[kind][0]).read_text()


def _norm(text: str) -> str:
    return text.replace("\r\n", "\n").strip()


def check(backend: Backend) -> list[dict]:
    srv = backend.server
    items: list[Item] = []
    try:
        trmm = backend.trmm
    except RuntimeError as e:
        return [asdict(Item("api", "TRMM-API-Key", "fehlt", str(e)))]

    # 1. Lesen
    missing = []
    for path, right in READ_CHECKS:
        try:
            trmm._request("GET", path)
        except TrmmError as e:
            if "HTTP 403" in str(e):
                missing.append(right)
            else:
                items.append(Item("api", f"TRMM {srv.trmm_url}", "fehler", str(e)))
                return [asdict(i) for i in items]
    if missing:
        items.append(Item("api", "Rechte des API-Keys", "fehlt",
                          "In der TRMM-Rolle fehlt: " + ", ".join(missing)
                          + ". Außerdem nötig: Run Scripts."))
        return [asdict(i) for i in items]
    items.append(Item("api", f"TRMM {srv.trmm_url}", "ok", "Lesen erlaubt (Run Scripts zeigt erst ein Test)"))

    # 1b. Schreibrechte, ohne etwas zu ändern (Anfrage an eine Kennung, die es nicht gibt)
    lacking = [right for method, path, right in WRITE_CHECKS if not trmm.may(method, path)]
    if lacking:
        items.append(Item("write", "Schreibrechte des API-Keys", "info",
                          "Fehlt: " + ", ".join(lacking) + ". Nur nötig für: "
                          + "; ".join(WRITE_USES[r] for r in lacking) + "."))
    else:
        items.append(Item("write", "Schreibrechte des API-Keys", "ok",
                          "Sites bearbeiten, Felder und Skripte anlegen erlaubt"))

    # 2. Felder an den Sites
    names = {f.get("name") for f in trmm.custom_fields() if f.get("model") == "site"}
    for fid, name, what in (("targets", srv.field_targets, "Ziele je Site, z. B. „NAS | 192.168.1.5:5001; https://fw.local“"),
                            ("agents", srv.field_agents, "Hostnamen bevorzugter Agenten, mit ; getrennt (optional)")):
        if name in names:
            items.append(Item(f"field-{fid}", f"Feld „{name}“ an Sites", "ok", what))
        else:
            items.append(Item(f"field-{fid}", f"Feld „{name}“ an Sites", "fehlt", what,
                              action=f"field-{fid}", action_label="In TRMM anlegen", writes_trmm=True))

    # 3. Skripte
    scripts = {s.get("name"): s for s in trmm.scripts()}
    for kind, name in (("start", srv.script_start), ("stop", srv.script_stop)):
        s = scripts.get(name)
        if s is None:
            items.append(Item(f"script-{kind}", f"Skript „{name}“", "fehlt", "",
                              action=f"script-{kind}", action_label="In TRMM anlegen", writes_trmm=True))
            continue
        body = trmm.script(s["id"]).get("script_body") or ""
        if _norm(body) == _norm(script_body(kind)):
            items.append(Item(f"script-{kind}", f"Skript „{name}“", "ok", "aktuell"))
        else:
            items.append(Item(f"script-{kind}", f"Skript „{name}“", "fehlt",
                              "veraltet oder von Hand geändert",
                              action=f"script-{kind}", action_label="In TRMM aktualisieren",
                              writes_trmm=True))

    # 4. Sprung-Host: Host-Schlüssel
    host, port = srv.jump_host, srv.jump_port
    hostkey_ok = False
    if not host:
        items.append(Item("hostkey", "Sprung-Host", "fehlt", "Adresse (host:port) eintragen"))
    else:
        known = hostkeys.stored(host, port)
        scan_error = ""
        try:
            scanned = hostkeys.scan(host, port)
        except RuntimeError as e:
            scanned = []
            scan_error = str(e)
        if not scanned:
            items.append(Item("hostkey", f"Sprung-Host {host}:{port}", "fehler", scan_error,
                              data={"fingerprints": hostkeys.fingerprints(known)}))
        elif not known:
            items.append(Item("hostkey", f"Sprung-Host {host}:{port}", "fehlt",
                              "Fingerabdruck mit der Ausgabe des Installers bzw. dem Log "
                              "des Sprung-Hosts vergleichen, dann bestätigen.",
                              action="hostkey", action_label="Fingerabdruck bestätigen",
                              data={"fingerprints": hostkeys.fingerprints(scanned), "lines": scanned}))
        elif set(_keys(scanned)) <= set(_keys(known)):
            hostkey_ok = True
            items.append(Item("hostkey", f"Sprung-Host {host}:{port}", "ok", "Host-Schlüssel bestätigt",
                              data={"fingerprints": hostkeys.fingerprints(known)}))
        else:
            items.append(Item("hostkey", f"Sprung-Host {host}:{port}", "fehler",
                              "Host-Schlüssel hat sich geändert! Nur bestätigen, wenn der Sprung-Host "
                              "neu aufgesetzt wurde.",
                              action="hostkey", action_label="Neuen Fingerabdruck bestätigen",
                              data={"fingerprints": hostkeys.fingerprints(scanned), "lines": scanned}))

    # 5. CA
    ca = certs.ca_public(srv)
    if ca:
        items.append(Item("ca", "CA dieses Clients", "ok",
                          "Diese Zeile muss beim Sprung-Host in TRUSTED_CA stehen.",
                          data={"ca": ca, "fingerprint": certs.fingerprint(ca)}))
    else:
        items.append(Item("ca", "CA dieses Clients", "fehlt",
                          "Mit der CA stellt der Client kurzlebige Zertifikate für Agenten und sich selbst aus.",
                          action="ca", action_label="CA erzeugen"))

    # 6. Anmeldung am Sprung-Host
    if ca and hostkey_ok:
        ok, detail = login_test(srv)
        items.append(Item("login", "Anmeldung am Sprung-Host", "ok" if ok else "fehler", detail))
    return [asdict(i) for i in items]


def _keys(lines: list[str]) -> list[str]:
    return [" ".join(l.split()[1:3]) for l in lines]


def login_test(srv: Server) -> tuple[bool, str]:
    who = f"{getpass.getuser()}@{socket.gethostname()}"
    cred = certs.issue(srv, ADMIN_USER, f"client test von={who}", minutes=5)
    with tempfile.TemporaryDirectory() as tmp:
        key, cert = certs.write_credential(cred, Path(tmp))
        known = Path(tmp) / "known_hosts"
        known.write_text(hostkeys.require(srv.jump_host, srv.jump_port))
        r = subprocess.run(
            ["ssh", "-T", "-F", "none", "-i", str(key), "-o", f"CertificateFile={cert}",
             "-o", "IdentitiesOnly=yes", "-o", "IdentityAgent=none",
             "-o", f"UserKnownHostsFile={known}", "-o", "GlobalKnownHostsFile=none",
             "-o", "StrictHostKeyChecking=yes", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10",
             "-p", str(srv.jump_port), f"{ADMIN_USER}@{srv.jump_host}", "true"],
            stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=30, check=False,
            **quiet(),
        )
    # sshd lässt keine Befehle zu (nologin, Status 1); 255 heißt: ssh selbst gescheitert
    if r.returncode != 255:
        return True, "Zertifikat wird akzeptiert"
    last = (r.stderr.strip().splitlines() or ["ohne Meldung"])[-1]
    hint = ""
    if "Permission denied" in last:
        hint = (" – Sprung-Host kennt diese CA noch nicht (TRUSTED_CA) oder dieser Rechner "
                "ist nicht in ADMIN_FROM")
    return False, last + hint


def run_action(backend: Backend, action: str, data: dict) -> str:
    srv = backend.server
    if action == "ca":
        _, created = certs.ensure_ca(srv)
        return "CA erzeugt" if created else "CA war schon vorhanden"
    if action == "hostkey":
        lines = [str(l) for l in data.get("lines", [])]
        fresh = hostkeys.scan(srv.jump_host, srv.jump_port)
        if not lines or set(_keys(lines)) != set(_keys(fresh)):
            raise RuntimeError("Host-Schlüssel hat sich seit der Anzeige geändert, bitte neu prüfen")
        hostkeys.store(srv.jump_host, srv.jump_port, fresh)
        return "Host-Schlüssel gespeichert"
    trmm = backend.trmm
    if action in ("field-targets", "field-agents"):
        name = srv.field_targets if action == "field-targets" else srv.field_agents
        trmm.create_site_field(name)
        return f"Feld „{name}“ angelegt"
    if action in ("script-start", "script-stop"):
        kind = action.split("-", 1)[1]
        name = srv.script_start if kind == "start" else srv.script_stop
        existing = next((s for s in trmm.scripts() if s.get("name") == name), None)
        body = {
            "name": name,
            "description": SCRIPTS[kind][1],
            "shell": "shell",
            "script_body": script_body(kind),
            "supported_platforms": ["linux", "darwin"],
            "default_timeout": 90,
            "args": [],
            "env_vars": [],
            "run_as_user": False,
        }
        trmm.save_script(existing["id"] if existing else None, body)
        backend.reload()
        return f"Skript „{name}“ " + ("aktualisiert" if existing else "angelegt")
    raise ValueError(f"Unbekannte Aktion {action}")
