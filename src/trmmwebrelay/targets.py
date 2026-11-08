# SPDX-License-Identifier: GPL-3.0-or-later
"""Ziele aus dem TRMM-Feld „Tunnel-Ziele“ lesen.

Format: Einträge getrennt mit `;` oder Zeilenumbruch, je Eintrag
`[Name |] Adresse`. Adresse ist eine URL (`https://192.168.1.1:8443/`)
oder nur `host[:port]`; dann erkennt der Client das Protokoll selbst.
"""

import ipaddress
import re
from dataclasses import dataclass
from urllib.parse import urlsplit


@dataclass(frozen=True)
class Target:
    raw: str
    addr: str  # Adresse ohne Name, wie eingetragen
    name: str
    scheme: str | None  # None: automatisch erkennen
    host: str
    port: int | None  # None: Standardport des Protokolls bzw. 443/80 probieren
    path: str

    def url(self, scheme: str | None = None, port: int | None = None) -> str:
        return make_url(scheme or self.scheme or "https", self.host, port or self.port, self.path)


def make_url(scheme: str, host: str, port: int | None, path: str = "/") -> str:
    h = f"[{host}]" if ":" in host else host
    default = {"http": 80, "https": 443}.get(scheme)
    netloc = h if port in (None, default) else f"{h}:{port}"
    return f"{scheme}://{netloc}{path or '/'}"


def parse_targets(value: str) -> tuple[list[Target], list[str]]:
    targets, errors = [], []
    for item in re.split(r"[;\n]", value or ""):
        item = item.strip()
        if not item:
            continue
        if "|" in item:
            name, addr = (part.strip() for part in item.split("|", 1))
        else:
            name, addr = "", item
        try:
            targets.append(_parse_addr(item, name, addr))
        except ValueError as e:
            errors.append(f"„{item}“: {e}")
    return targets, errors


def _parse_addr(raw: str, name: str, addr: str) -> Target:
    scheme = None
    if "://" in addr:
        parts = urlsplit(addr)
        scheme = parts.scheme.lower()
        if scheme not in ("http", "https"):
            raise ValueError(f"Protokoll {scheme} wird nicht unterstützt")
    else:
        parts = urlsplit("//" + addr)
    host = (parts.hostname or "").lower()
    if not host:
        raise ValueError("kein Host angegeben")
    try:
        port = parts.port
    except ValueError:
        raise ValueError("ungültiger Port") from None
    path = parts.path or "/"
    if parts.query:
        path += "?" + parts.query
    return Target(raw=raw, addr=addr, name=name, scheme=scheme, host=host, port=port, path=path)


def parse_agent_list(value: str) -> list[str]:
    return [p.lower() for p in re.split(r"[;,\s]+", value or "") if p]


def is_ip(host: str) -> bool:
    try:
        ipaddress.ip_address(host)
        return True
    except ValueError:
        return False


def networks_from_local_ips(local_ips: str) -> list[ipaddress.IPv4Network]:
    """Private IPv4-Netze des Tunnel-Agenten (ab /16), z. B. aus "192.168.1.10/24, fe80::…"."""
    nets = []
    for part in re.split(r"[,\s]+", local_ips or ""):
        if "/" not in part:
            continue
        try:
            iface = ipaddress.ip_interface(part)
        except ValueError:
            continue
        net = iface.network
        if (
            net.version == 4
            and net.is_private
            and not net.is_loopback
            and not net.is_link_local
            and net.prefixlen >= 16
            and net not in nets
        ):
            nets.append(net)
    return nets


def format_targets(items: list[tuple[str, str]]) -> str:
    """Ziele als Wert für das Feld „Tunnel-Ziele“; wirft ValueError bei ungültigen Einträgen."""
    parts = []
    for name, addr in items:
        name, addr = name.strip(), addr.strip()
        if not addr:
            if name:
                raise ValueError(f"„{name}“: Adresse fehlt")
            continue
        if any(c in name for c in "|;\n") or any(c in addr for c in "|; \n"):
            raise ValueError(f"„{name or addr}“: | ; und Leerzeichen sind nicht erlaubt")
        entry = f"{name} | {addr}" if name else addr
        _parse_addr(entry, name, addr)  # gleiche Prüfung wie beim Lesen
        parts.append(entry)
    return "; ".join(parts)


def format_agent_list(names: list[str]) -> str:
    clean = []
    for n in names:
        n = n.strip().lower()
        if not n:
            continue
        if not re.fullmatch(r"[a-z0-9][a-z0-9._-]*", n):
            raise ValueError(f"„{n}“ ist kein Hostname")
        if n not in clean:
            clean.append(n)
    return "; ".join(clean)
