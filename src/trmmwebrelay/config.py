# SPDX-License-Identifier: GPL-3.0-or-later
"""Einstellungen aus ~/.config/trmm-web-relay/config.toml (ohne Geheimnisse).

Ein Client kann mehrere TRMM-Server nutzen (je MSP bzw. Instanz ein
Abschnitt [[server]] mit eigenem Sprung-Host, API-Key und CA).
"""

import os
import re
import tomllib
from dataclasses import dataclass, field, fields
from pathlib import Path

CONFIG_PATH = Path(
    os.environ.get("TRMM_WEB_RELAY_CONFIG", "~/.config/trmm-web-relay/config.toml")
).expanduser()
STATE_DIR = Path("~/.local/share/trmm-web-relay").expanduser()
CACHE_DIR = Path("~/.cache/trmm-web-relay").expanduser()

# Feste Konten auf dem Sprung-Host
ADMIN_USER = "wr-admin"  # Client, nur lokale Weiterleitung (-L)
TUNNEL_USER = "wr-tunnel"  # Agenten, nur Fernweiterleitung (-R)

DEFAULT_UPDATE_URL = "https://code.bashclub.org/bashclub/trmm-web-relay/raw/branch/main/pyproject.toml"

_HOST_RE = re.compile(r"^(\*\.)?[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)*$")

_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,31}$")


@dataclass
class Server:
    id: str  # kurz, für Schlüsselnamen: [a-z0-9-]
    name: str
    trmm_url: str
    jump: str = ""  # host:port des Sprung-Hosts
    remote_port_base: int = 20000  # wie REMOTE_PORT_BASE am Sprung-Host
    field_targets: str = "Tunnel-Ziele"
    field_agents: str = "Tunnel-Agent"
    script_start: str = "Web-Relay: Tunnel starten"
    script_stop: str = "Web-Relay: Tunnel stoppen"

    @property
    def jump_host(self) -> str:
        return split_hostport(self.jump)[0]

    @property
    def jump_port(self) -> int:
        return split_hostport(self.jump)[1]

    @property
    def api_key_name(self) -> str:
        return f"trmm-web-relay-{self.id}-api-key"

    @property
    def ca_key_name(self) -> str:
        return f"trmm-web-relay-{self.id}-ca"


@dataclass
class Config:
    control_port: int = 8765
    socks_port: int = 8766
    idle_minutes: int = 30
    max_hours: int = 4
    # Leer: Brave bzw. Chromium automatisch suchen
    browser: str = ""
    # Hosts, die das Browserprofil direkt (ohne Tunnel) erreicht, z. B. ein
    # Passwortmanager; "host" gilt mit Subdomains, nur Port 443 außer mit ":port"
    direct_hosts: list[str] = field(default_factory=list)
    # Web Store und Updates für Browser-Erweiterungen direkt erreichbar
    extension_store: bool = True
    # Alte Arbeitsweise: Zertifikatsfehler im Profil ignorieren (auch bei direct_hosts)
    ignore_cert_errors: bool = False
    # Quelle für den Hinweis auf neue Versionen (leer: keine Abfrage)
    update_url: str = DEFAULT_UPDATE_URL
    # Server, dessen Sites die Steuerseite zeigt (immer nur einer)
    active_server: str = ""
    servers: list[Server] = field(default_factory=list)

    def server(self, server_id: str) -> Server | None:
        return next((s for s in self.servers if s.id == server_id), None)

    @property
    def active(self) -> Server | None:
        return self.server(self.active_server) or (self.servers[0] if self.servers else None)


DEFAULT_JUMP_PORT = 22222


def split_hostport(value: str) -> tuple[str, int]:
    value = value.strip()
    if not value:
        return "", DEFAULT_JUMP_PORT
    host, sep, port = value.rpartition(":")
    if sep and port.isdigit() and host and not host.endswith(":"):
        return host.strip("[]"), int(port)
    return value.strip("[]"), DEFAULT_JUMP_PORT


def normalize_direct_hosts(entries) -> list[str]:
    """Prüft Einträge für direct_hosts (host, *.host, host:port); wirft ValueError."""
    if isinstance(entries, str):
        entries = entries.replace(",", " ").split()
    if not isinstance(entries, list):
        raise ValueError("direct_hosts: Liste von Hostnamen erwartet")
    out = []
    for raw in entries:
        if not isinstance(raw, str):
            raise ValueError("direct_hosts: Liste von Hostnamen erwartet")
        entry = raw.strip().lower().rstrip(".")
        if not entry:
            continue
        if "://" in entry or "/" in entry:
            raise ValueError(f"„{raw}“: nur Hostname ohne https:// und Pfad, optional mit :port")
        host, sep, port = entry.rpartition(":")
        if not sep:
            host, port = entry, ""
        if port and not (port.isdigit() and 0 < int(port) < 65536):
            raise ValueError(f"„{raw}“: ungültiger Port")
        if not _HOST_RE.match(host):
            raise ValueError(f"„{raw}“: nur Hostname, optional mit :port (z. B. vault.example.com:8443)")
        value = f"{host}:{port}" if port else host
        if value not in out:
            out.append(value)
    return out


def valid_id(value: str) -> bool:
    return bool(_ID_RE.match(value))


def make_id(name: str, taken: set[str]) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:24] or "server"
    if not base[0].isalnum():
        base = "s" + base
    candidate, n = base, 2
    while candidate in taken:
        candidate, n = f"{base}-{n}", n + 1
    return candidate


def _apply(target, data: dict, section: str, skip: tuple = ()) -> None:
    known = {f.name for f in fields(target)} - set(skip)
    for key, value in data.items():
        if key not in known:
            raise ValueError(f"Unbekannte Einstellung in {CONFIG_PATH}: {section}{key}")
        setattr(target, key, value)


def load() -> Config:
    cfg = Config()
    if not CONFIG_PATH.exists():
        return cfg
    data = tomllib.loads(CONFIG_PATH.read_text())
    servers = data.pop("server", [])
    _apply(cfg, data, "", skip=("servers",))
    try:
        cfg.direct_hosts = normalize_direct_hosts(cfg.direct_hosts)
    except ValueError as e:
        raise ValueError(f"{CONFIG_PATH}: {e}") from None
    if not isinstance(cfg.update_url, str):
        raise ValueError(f"update_url in {CONFIG_PATH}: Adresse als Text erwartet")
    for flag in ("extension_store", "ignore_cert_errors"):
        if not isinstance(getattr(cfg, flag), bool):
            raise ValueError(f"{flag} in {CONFIG_PATH}: true oder false erwartet")
    for i, raw in enumerate(servers):
        srv = Server(id=raw.get("id", ""), name=raw.get("name", ""), trmm_url=raw.get("trmm_url", ""))
        _apply(srv, raw, f"server[{i}].")
        if not valid_id(srv.id):
            raise ValueError(f"server[{i}].id „{srv.id}“: nur a-z, 0-9 und -")
        if cfg.server(srv.id):
            raise ValueError(f"server[{i}].id „{srv.id}“ doppelt")
        srv.trmm_url = srv.trmm_url.rstrip("/")
        srv.name = srv.name or srv.id
        cfg.servers.append(srv)
    return cfg


def _toml_value(v) -> str:
    if isinstance(v, list):
        return "[" + ", ".join(_toml_value(x) for x in v) + "]"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        return str(v)
    s = str(v).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{s}"'


def save(cfg: Config) -> None:
    """Schreibt die Konfiguration; nur Werte, die vom Standard abweichen (außer Pflichtfeldern)."""
    default, default_srv = Config(), Server(id="", name="", trmm_url="")
    lines = [
        "# TRMM Web-Relay. Keine Geheimnisse hier: API-Keys und CA liegen im",
        "# Schlüsselbund. Bearbeiten am einfachsten über die Einrichtung im Client.",
        "",
    ]
    for f in fields(cfg):
        if f.name == "servers":
            continue
        value = getattr(cfg, f.name)
        if value != getattr(default, f.name):
            lines.append(f"{f.name} = {_toml_value(value)}")
    for srv in cfg.servers:
        lines += ["", "[[server]]"]
        for f in fields(srv):
            value = getattr(srv, f.name)
            if f.name in ("id", "name", "trmm_url", "jump") or value != getattr(default_srv, f.name):
                lines.append(f"{f.name} = {_toml_value(value)}")
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = CONFIG_PATH.with_suffix(".tmp")
    tmp.write_text("\n".join(lines) + "\n")
    tmp.replace(CONFIG_PATH)
