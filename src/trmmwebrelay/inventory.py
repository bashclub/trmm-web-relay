# SPDX-License-Identifier: GPL-3.0-or-later
"""Kunden, Sites, Ziele und Agenten aus TRMM (kein eigenes Inventar)."""

from dataclasses import dataclass, field

from trmmwebrelay.config import Server
from trmmwebrelay.targets import Target, parse_agent_list, parse_targets
from trmmwebrelay.trmm import Trmm

# Für diese Plattformen gibt es das Tunnel-Skript (Shell)
SUPPORTED_PLATFORMS = ("linux", "darwin")


@dataclass
class Agent:
    agent_id: str
    hostname: str
    plat: str
    monitoring_type: str
    status: str
    local_ips: str
    client: str
    site: str

    @classmethod
    def from_api(cls, a: dict) -> "Agent":
        return cls(
            agent_id=a["agent_id"],
            hostname=a.get("hostname") or "",
            plat=a.get("plat") or "",
            monitoring_type=a.get("monitoring_type") or "",
            status=a.get("status") or "",
            local_ips=a.get("local_ips") or "",
            client=a.get("client_name") or "",
            site=a.get("site_name") or "",
        )


@dataclass
class Site:
    server_id: str
    id: int
    client: str
    name: str
    targets: list[Target] = field(default_factory=list)
    target_errors: list[str] = field(default_factory=list)
    preferred_agents: list[str] = field(default_factory=list)

    @property
    def key(self) -> str:
        return f"{self.server_id}/{self.id}"


def _field_id(fields: list[dict], name: str) -> int | None:
    for f in fields:
        if f.get("model") == "site" and f.get("name") == name:
            return f["id"]
    return None


def site_field_ids(trmm: Trmm, cfg: Server) -> tuple[int | None, int | None]:
    """IDs der Felder „Tunnel-Ziele“ und „Tunnel-Agent“ (None, wenn es sie nicht gibt)."""
    fields = trmm.custom_fields()
    return _field_id(fields, cfg.field_targets), _field_id(fields, cfg.field_agents)


def load_sites(trmm: Trmm, cfg: Server) -> list[Site]:
    fid_targets, fid_agents = site_field_ids(trmm, cfg)
    if fid_targets is None:
        raise RuntimeError(f"Benutzerfeld „{cfg.field_targets}“ an Sites fehlt in TRMM")
    sites = []
    for client in trmm.clients():
        for s in client.get("sites", []):
            values = {cf["field"]: cf.get("value") or "" for cf in s.get("custom_fields", [])}
            targets, errors = parse_targets(values.get(fid_targets, ""))
            sites.append(
                Site(
                    server_id=cfg.id,
                    id=s["id"],
                    client=client["name"],
                    name=s["name"],
                    targets=targets,
                    target_errors=errors,
                    preferred_agents=parse_agent_list(values.get(fid_agents, ""))
                    if fid_agents is not None
                    else [],
                )
            )
    return sorted(sites, key=lambda s: (s.client.lower(), s.name.lower()))


def agents_of(site: Site, agents: list[Agent]) -> list[Agent]:
    return [a for a in agents if a.client == site.client and a.site == site.name]


def choose_agent(site: Site, agents: list[Agent]) -> tuple[Agent | None, list[str]]:
    """Erster Agent der Prioritätsliste, der online ist; sonst ein Server der Site.

    Gibt den Agenten und Hinweise (übersprungene Einträge) zurück.
    """
    notes = []
    mine = agents_of(site, agents)
    by_name = {a.hostname.lower(): a for a in mine}
    for name in site.preferred_agents:
        a = by_name.get(name)
        if a is None:
            notes.append(f"{name}: kein TRMM-Agent")
        elif a.status != "online":
            notes.append(f"{name}: {a.status}")
        elif a.plat not in SUPPORTED_PLATFORMS:
            notes.append(f"{name}: {a.plat} wird noch nicht unterstützt")
        else:
            return a, notes
    usable = [a for a in mine if a.status == "online" and a.plat in SUPPORTED_PLATFORMS]
    usable.sort(key=lambda a: (a.monitoring_type != "server", a.hostname.lower()))
    if usable:
        if site.preferred_agents:
            notes.append(f"Ausweichen auf {usable[0].hostname}")
        return usable[0], notes
    notes.append("kein passender Agent online (Linux oder macOS)")
    return None, notes
