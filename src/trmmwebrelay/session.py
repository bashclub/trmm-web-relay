# SPDX-License-Identifier: GPL-3.0-or-later
"""Sitzungen: Tunnel über TRMM starten, lokal anbinden, überwachen, beenden."""

import base64
import getpass
import ipaddress
import logging
import secrets
import shutil
import socket
import subprocess
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

from trmmwebrelay import certs, hostkeys
from trmmwebrelay.config import ADMIN_USER, TUNNEL_USER, Config
from trmmwebrelay.detect import Detected, detect, load_cache, save_cache
from trmmwebrelay.inventory import Agent, Site, choose_agent
from trmmwebrelay.platform import detached
from trmmwebrelay.servers import Backend, Registry
from trmmwebrelay.socks import probe
from trmmwebrelay.targets import is_ip, networks_from_local_ips

log = logging.getLogger(__name__)

READY_TIMEOUT = 90  # Sekunden bis der Tunnel vom Agenten stehen muss


@dataclass
class ResolvedTarget:
    name: str
    url: str
    title: str
    error: str = ""


@dataclass
class Session:
    id: str
    site: Site
    backend: Backend
    agent: Agent | None = None
    state: str = "startet"  # startet, bereit, beendet, fehler
    message: str = ""
    notes: list[str] = field(default_factory=list)
    local_port: int = 0
    remote_port: int = 0
    started: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)
    networks: list = field(default_factory=list)
    hostnames: set = field(default_factory=set)
    targets: list[ResolvedTarget] = field(default_factory=list)
    proc: subprocess.Popen | None = None
    ssh_log: Path | None = None
    work_dir: Path | None = None  # Wegwerf-Schlüssel des Clients
    remote_started: bool = False

    def touch(self) -> None:
        self.last_activity = time.time()

    @property
    def active(self) -> bool:
        return self.state in ("startet", "bereit")

    def matches(self, host: str) -> int:
        """Länge des passenden Präfixes (Hostname: 129), 0 wenn nicht zuständig."""
        host = host.lower().rstrip(".")
        if host in self.hostnames:
            return 129
        try:
            ip = ipaddress.ip_address(host)
        except ValueError:
            return 0
        best = 0
        for net in self.networks:
            if ip.version == net.version and ip in net:
                best = max(best, net.prefixlen)
        return best


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class SessionManager:
    def __init__(self, cfg: Config, registry: Registry):
        self.cfg = cfg
        self.registry = registry
        self.sessions: dict[str, Session] = {}
        self.lock = threading.RLock()
        threading.Thread(target=self._watchdog, daemon=True, name="watchdog").start()

    # --- Verteiler -------------------------------------------------------

    def resolve(self, host: str) -> Session | None:
        best, best_len = None, 0
        with self.lock:
            for s in self.sessions.values():
                if s.state != "bereit":
                    continue
                n = s.matches(host)
                if n > best_len or (n == best_len and n and s.started > best.started):
                    best, best_len = s, n
        return best

    # --- Ablauf ----------------------------------------------------------

    def active_for_site(self, key: str) -> Session | None:
        with self.lock:
            for s in self.sessions.values():
                if s.site.key == key and s.active:
                    return s
        return None

    def start(self, backend: Backend, site: Site) -> Session:
        with self.lock:
            existing = self.active_for_site(site.key)
            if existing:
                return existing
            sess = Session(id=secrets.token_hex(8), site=site, backend=backend)
            # beendete Sitzungen derselben Site aus der Anzeige nehmen
            for sid in [k for k, v in self.sessions.items() if v.site.key == site.key]:
                del self.sessions[sid]
            self.sessions[sess.id] = sess
        threading.Thread(target=self._run, args=(sess,), daemon=True, name=f"s-{sess.id}").start()
        return sess

    def _run(self, sess: Session) -> None:
        cfg, backend = self.cfg, sess.backend
        server = backend.server
        try:
            host, port = server.jump_host, server.jump_port
            if not host:
                raise RuntimeError(f"Sprung-Host für {server.name} fehlt (Einrichtung)")
            trmm = backend.trmm
            site = sess.site
            sess.message = "Agent wählen"
            agents = [Agent.from_api(a) for a in trmm.agents()]
            agent, notes = choose_agent(site, agents)
            sess.notes = notes
            if agent is None:
                raise RuntimeError("Kein Agent für den Tunnel verfügbar")
            sess.agent = agent

            known = hostkeys.require(host, port)
            start_id = backend.script_id(server.script_start)
            backend.script_id(server.script_stop)
            who = f"{getpass.getuser()}@{socket.gethostname()}"
            # Zertifikat für den Agenten: nur zum Anmelden, wenige Minuten gültig
            agent_cred = certs.issue(
                server, certs.site_principal(site.id),
                f"site-{site.id} {agent.hostname} sitzung={sess.id} von={who}",
            )
            admin_cred = certs.issue(server, ADMIN_USER, f"client sitzung={sess.id} von={who}")

            sess.remote_port = server.remote_port_base + site.id
            sess.local_port = _free_port()
            sess.message = f"Tunnel auf {agent.hostname} starten"
            trmm.run_script(
                agent.agent_id,
                start_id,
                args=[sess.id, host, str(port), TUNNEL_USER, str(sess.remote_port)],
                env_vars=[
                    "WR_KEY=" + base64.b64encode(agent_cred.key.encode()).decode(),
                    "WR_CERT=" + base64.b64encode(agent_cred.cert.encode() + b"\n").decode(),
                    "WR_KNOWN_HOSTS=" + base64.b64encode(known.encode()).decode(),
                ],
                timeout=cfg.max_hours * 3600,
            )
            sess.remote_started = True

            sess.message = "Mit dem Sprung-Host verbinden"
            sess.work_dir = Path(tempfile.mkdtemp(prefix=f"wr-{sess.id}-"))
            key_path, cert_path = certs.write_credential(admin_cred, sess.work_dir)
            known_path = sess.work_dir / "known_hosts"
            known_path.write_text(known)
            sess.ssh_log = sess.work_dir / "ssh.log"
            with open(sess.ssh_log, "w") as logf:
                sess.proc = subprocess.Popen(
                    [
                        "ssh", "-N", "-T", "-F", "none",
                        "-i", str(key_path), "-o", f"CertificateFile={cert_path}",
                        "-o", "IdentitiesOnly=yes", "-o", "IdentityAgent=none",
                        "-o", f"UserKnownHostsFile={known_path}",
                        "-o", "GlobalKnownHostsFile=none",
                        "-o", "StrictHostKeyChecking=yes",
                        "-o", "BatchMode=yes",
                        "-o", "ExitOnForwardFailure=yes",
                        "-o", "ServerAliveInterval=15",
                        "-o", "ServerAliveCountMax=3",
                        "-o", "ConnectTimeout=15",
                        "-p", str(port),
                        "-L", f"127.0.0.1:{sess.local_port}:127.0.0.1:{sess.remote_port}",
                        f"{ADMIN_USER}@{host}",
                    ],
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=logf,
                    **detached(),
                )

            sess.message = f"Warten auf den Tunnel von {agent.hostname}"
            deadline = time.time() + READY_TIMEOUT
            while not probe(sess.local_port):
                if sess.state != "startet":
                    return  # inzwischen beendet
                if sess.proc.poll() is not None:
                    raise RuntimeError("SSH zum Sprung-Host beendet: " + self._ssh_error(sess))
                if time.time() > deadline:
                    raise RuntimeError(
                        f"Tunnel vom Agenten kam nicht innerhalb von {READY_TIMEOUT} s an "
                        "(Skriptverlauf in TRMM prüfen; „Permission denied“: Absender des "
                        "Agenten noch nicht freigegeben, der Sprung-Host gleicht alle 5 min mit TRMM ab)"
                    )
                time.sleep(1)

            sess.networks = networks_from_local_ips(agent.local_ips)
            for t in site.targets:
                if is_ip(t.host):
                    ip = ipaddress.ip_address(t.host)
                    if not any(ip in n for n in sess.networks if n.version == ip.version):
                        sess.networks.append(ipaddress.ip_network(t.host))
                else:
                    sess.hostnames.add(t.host)

            # Schlüssel des Clients wird nach der Anmeldung nicht mehr gebraucht
            key_path.unlink(missing_ok=True)

            sess.message = "Ziele erkennen"
            cache = load_cache()
            sess.targets = [self._resolved(t, cache.get(f"{site.key}|{t.raw}")) for t in site.targets]
            sess.touch()
            sess.state = "bereit"
            sess.message = ""
            self._detect_all(sess)
        except Exception as e:  # noqa: BLE001 - Fehler in der Oberfläche zeigen
            log.warning("Sitzung %s: %s", sess.id, e)
            self.stop(sess.id, str(e), failed=True)

    @staticmethod
    def _resolved(t, d: Detected | None) -> ResolvedTarget:
        if d and not d.error:
            return ResolvedTarget(name=t.name or d.title or t.addr, url=d.url, title=d.title)
        return ResolvedTarget(name=t.name or t.addr, url=t.url(), title="", error="")

    def _detect_all(self, sess: Session) -> None:
        def one(i_t):
            i, t = i_t
            d = detect(sess.local_port, t)
            if not d.error:
                save_cache(f"{sess.site.key}|{t.raw}", d)
            sess.targets[i] = ResolvedTarget(
                name=t.name or d.title or t.addr, url=d.url, title=d.title, error=d.error
            )

        with ThreadPoolExecutor(max_workers=8) as pool:
            list(pool.map(one, enumerate(sess.site.targets)))

    @staticmethod
    def _ssh_error(sess: Session) -> str:
        try:
            text = sess.ssh_log.read_text().strip() if sess.ssh_log else ""
        except OSError:
            text = ""
        return text.splitlines()[-1] if text else "ohne Meldung"

    def stop(self, sid: str, reason: str = "beendet", failed: bool = False) -> None:
        with self.lock:
            sess = self.sessions.get(sid)
            if sess is None or not sess.active:
                return
            sess.state = "fehler" if failed else "beendet"
            sess.message = reason
        if sess.remote_started and sess.agent:
            try:
                backend = sess.backend
                backend.trmm.run_script(
                    sess.agent.agent_id,
                    backend.script_id(backend.server.script_stop),
                    args=[sess.id],
                    env_vars=[],
                    timeout=60,
                )
            except Exception as e:  # noqa: BLE001
                log.warning("Stopp-Skript für %s fehlgeschlagen: %s", sid, e)
                sess.message += f" (Stopp-Skript: {e}; Laufzeitgrenze greift trotzdem)"
        if sess.proc and sess.proc.poll() is None:
            sess.proc.terminate()
            try:
                sess.proc.wait(5)
            except subprocess.TimeoutExpired:
                sess.proc.kill()
        if sess.work_dir:
            shutil.rmtree(sess.work_dir, ignore_errors=True)

    def stop_all(self, reason: str) -> None:
        for sid in list(self.sessions):
            self.stop(sid, reason)

    def _watchdog(self) -> None:
        while True:
            time.sleep(10)
            now = time.time()
            for sess in list(self.sessions.values()):
                if sess.state != "bereit":
                    continue
                if sess.proc and sess.proc.poll() is not None:
                    self.stop(sess.id, "SSH-Verbindung getrennt: " + self._ssh_error(sess), failed=True)
                elif now - sess.last_activity > self.cfg.idle_minutes * 60:
                    self.stop(sess.id, f"nach {self.cfg.idle_minutes} min Leerlauf beendet")
                elif now - sess.started > self.cfg.max_hours * 3600:
                    self.stop(sess.id, f"Höchstdauer {self.cfg.max_hours} h erreicht")
