# SPDX-License-Identifier: GPL-3.0-or-later
"""Steuerseite auf http://127.0.0.1:<control_port>/ (Sites und Einrichtung)."""

import json
import logging
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from trmmwebrelay import browser, certs, config, hostkeys, installer, inventory, keystore, setup, version
from trmmwebrelay.config import Config, Server
from trmmwebrelay.servers import Registry
from trmmwebrelay.session import Session, SessionManager
from trmmwebrelay.targets import format_agent_list, format_targets
from trmmwebrelay.trmm import TrmmError

log = logging.getLogger(__name__)
STATIC = Path(__file__).parent / "static"
APP_ID = "trmm-web-relay"


class App:
    def __init__(self, cfg: Config, registry: Registry, manager: SessionManager):
        self.cfg = cfg
        self.registry = registry
        self.manager = manager
        self.quit = threading.Event()
        self._cfg_lock = threading.Lock()

    # --- Sites -----------------------------------------------------------

    def _session_json(self, s: Session | None) -> dict | None:
        if s is None:
            return None
        now = time.time()
        return {
            "id": s.id,
            "state": s.state,
            "message": s.message,
            "notes": s.notes,
            "agent": s.agent.hostname if s.agent else "",
            "started": s.started,
            "idle_left": max(0, int(self.cfg.idle_minutes * 60 - (now - s.last_activity))),
            "max_left": max(0, int(self.cfg.max_hours * 3600 - (now - s.started))),
            "networks": [str(n) for n in s.networks],
            "targets": [t.__dict__ for t in s.targets],
        }

    def state(self) -> dict:
        """Nur der aktive Server mit Sites; die anderen nur zum Umschalten."""
        sessions = {s.site.key: s for s in self.manager.sessions.values()}
        active = self.cfg.active
        b = self.registry.get(active.id) if active else None
        return {
            "configured": bool(self.cfg.servers),
            "servers": [{"id": s.id, "name": s.name} for s in self.cfg.servers],
            "active": active.id if active else "",
            "error": b.error if b else "",
            "loaded_at": b.loaded_at if b else 0,
            "active_sessions": sum(1 for s in self.manager.sessions.values() if s.active),
            "version": version.status(self.cfg),
            "sites": [
                {
                    "id": s.id,
                    "client": s.client,
                    "name": s.name,
                    "targets": [{"raw": t.raw, "addr": t.addr, "name": t.name} for t in s.targets],
                    "target_errors": s.target_errors,
                    "agents": s.preferred_agents,
                    "session": self._session_json(sessions.get(s.key)),
                }
                for s in (b.sites if b else [])
            ],
        }

    def active_backend(self):
        srv = self.cfg.active
        if srv is None:
            raise LookupError("Kein Server eingerichtet")
        return self.backend(srv.id)

    def switch(self, server_id: str) -> None:
        """Auf einen anderen TRMM-Server umschalten; offene Tunnel werden beendet."""
        if self.cfg.server(server_id) is None:
            raise LookupError("Server unbekannt")
        if server_id == (self.cfg.active.id if self.cfg.active else ""):
            return
        for s in list(self.manager.sessions.values()):
            self.manager.stop(s.id, "auf anderen Server umgeschaltet")
        with self.manager.lock:
            self.manager.sessions.clear()
        with self._cfg_lock:
            self.cfg.active_server = server_id
            config.save(self.cfg)
        log.info("Umgeschaltet auf %s", self.cfg.active.name)
        self.backend(server_id).reload()

    # --- Site bearbeiten (schreibt die Felder in TRMM, Recht: Manage Sites) ---

    def site_agents(self, site_id: int) -> list[dict]:
        b = self.active_backend()
        site = b.site(site_id)
        if site is None:
            raise LookupError("Site unbekannt")
        agents = [inventory.Agent.from_api(a) for a in b.trmm.agents()]
        return sorted(
            ({"hostname": a.hostname.lower(), "plat": a.plat, "status": a.status,
              "type": a.monitoring_type,
              "usable": a.plat in inventory.SUPPORTED_PLATFORMS}
             for a in inventory.agents_of(site, agents)),
            key=lambda a: (not a["usable"], a["type"] != "server", a["hostname"]),
        )

    def save_site(self, body: dict) -> None:
        b = self.active_backend()
        site_id = int(body["site_id"])
        if b.site(site_id) is None:
            raise LookupError("Site unbekannt")
        targets = format_targets([(str(t.get("name", "")), str(t.get("addr", ""))) for t in body.get("targets", [])])
        agents = format_agent_list([str(a) for a in body.get("agents", [])])
        trmm = b.trmm
        fid_targets, fid_agents = inventory.site_field_ids(trmm, b.server)
        if fid_targets is None:
            raise LookupError(f"Feld „{b.server.field_targets}“ fehlt in TRMM (Einrichtung)")
        values = {fid_targets: targets}
        if fid_agents is not None:
            values[fid_agents] = agents
        elif agents:
            raise LookupError(f"Feld „{b.server.field_agents}“ fehlt in TRMM (Einrichtung)")
        try:
            trmm.set_site_fields(site_id, values)
        except TrmmError as e:
            if "HTTP 403" in str(e):
                raise ValueError("Der API-Key darf Sites nicht ändern (TRMM-Recht „Manage Sites“ fehlt)") from None
            raise
        log.info("%s: Site %s bearbeitet", b.server.name, site_id)
        b.reload()

    # --- Einrichtung -----------------------------------------------------

    def setup_state(self) -> dict:
        return {
            "servers": [
                {
                    "id": s.id,
                    "name": s.name,
                    "trmm_url": s.trmm_url,
                    "jump": s.jump,
                    "has_key": bool(keystore.get(s.api_key_name)),
                    "has_ca": bool(certs.ca_public(s)),
                }
                for s in self.cfg.servers
            ],
            "config_path": str(config.CONFIG_PATH),
            "profile": {
                "direct_hosts": self.cfg.direct_hosts,
                "extension_store": self.cfg.extension_store,
                "ignore_cert_errors": self.cfg.ignore_cert_errors,
            },
        }

    def save_profile(self, body: dict) -> str:
        """Einstellungen des Browserprofils; der Verteiler nutzt sie sofort."""
        hosts = config.normalize_direct_hosts(body.get("direct_hosts", []))
        store = bool(body.get("extension_store", True))
        ignore = bool(body.get("ignore_cert_errors", False))
        with self._cfg_lock:
            cert_changed = ignore != self.cfg.ignore_cert_errors
            self.cfg.direct_hosts = hosts
            self.cfg.extension_store = store
            self.cfg.ignore_cert_errors = ignore
            config.save(self.cfg)
        log.info("Browserprofil: direct_hosts=%s, extension_store=%s, ignore_cert_errors=%s", hosts, store, ignore)
        msg = "Gespeichert, gilt sofort."
        if cert_changed:
            msg += " Die Zertifikatsprüfung ändert sich erst, wenn alle Fenster des Profils geschlossen waren."
        return msg

    def save_server(self, body: dict) -> str:
        name = str(body.get("name", "")).strip()
        url = str(body.get("trmm_url", "")).strip().rstrip("/")
        jump = str(body.get("jump", "")).strip()
        api_key = str(body.get("api_key", "")).strip()
        if not name:
            raise ValueError("Name fehlt")
        if not url.startswith("https://"):
            raise ValueError("TRMM-API-Adresse muss mit https:// beginnen")
        host, port = config.split_hostport(jump)
        if jump and (not host or not 0 < port < 65536):
            raise ValueError("Sprung-Host als host:port angeben")
        with self._cfg_lock:
            srv = self.cfg.server(str(body.get("id") or ""))
            if srv is None:
                if not api_key:
                    raise ValueError("API-Key fehlt")
                srv = Server(id=config.make_id(name, {s.id for s in self.cfg.servers}), name=name, trmm_url=url)
                self.cfg.servers.append(srv)
            srv.name, srv.trmm_url = name, url
            srv.jump = f"{host}:{port}" if host else ""
            if api_key:
                keystore.put(srv.api_key_name, api_key)
            config.save(self.cfg)
            self.registry.sync()
        backend = self.registry.get(srv.id)
        threading.Thread(target=backend.reload, daemon=True).start()
        return srv.id

    def delete_server(self, server_id: str) -> None:
        with self._cfg_lock:
            srv = self.cfg.server(server_id)
            if srv is None:
                return
            for s in list(self.manager.sessions.values()):
                if s.site.server_id == server_id:
                    self.manager.stop(s.id, "Server entfernt")
            self.cfg.servers.remove(srv)
            if self.cfg.active_server == server_id:
                self.cfg.active_server = ""
            config.save(self.cfg)
            self.registry.sync()
            for name in (srv.api_key_name, srv.ca_key_name, srv.ca_key_name + ".pub"):
                keystore.delete(name)

    def backend(self, server_id: str):
        b = self.registry.get(str(server_id))
        if b is None:
            raise LookupError("Server unbekannt")
        return b


def make_handler(app: App):
    allowed_hosts = {f"127.0.0.1:{app.cfg.control_port}", f"localhost:{app.cfg.control_port}"}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            log.debug("web: " + fmt, *args)

        def _send(self, code: int, body: bytes, ctype: str, extra: dict | None = None) -> None:
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'")
            for k, v in (extra or {}).items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(body)

        def _json(self, code: int, data) -> None:
            self._send(code, json.dumps(data, ensure_ascii=False).encode(), "application/json")

        def _host_ok(self) -> bool:
            # Schutz gegen DNS-Rebinding
            return self.headers.get("Host", "") in allowed_hosts

        def do_GET(self):
            if not self._host_ok():
                return self._send(403, b"forbidden", "text/plain")
            url = urlsplit(self.path)
            if url.path in ("/", "/einrichtung"):
                page = "index.html" if url.path == "/" else "setup.html"
                return self._send(200, (STATIC / page).read_bytes(), "text/html; charset=utf-8")
            if url.path == "/icon.svg":
                return self._send(200, (STATIC / "icon.svg").read_bytes(), "image/svg+xml")
            if url.path == "/api/ping":
                return self._json(200, {"app": APP_ID})
            if url.path == "/api/state":
                return self._json(200, app.state())
            if url.path == "/api/site/agents":
                try:
                    site_id = int(parse_qs(url.query).get("site", ["0"])[0])
                    return self._json(200, {"agents": app.site_agents(site_id)})
                except (ValueError, LookupError) as e:
                    return self._json(400, {"error": str(e)})
                except Exception as e:  # noqa: BLE001
                    return self._json(500, {"error": str(e)})
            if url.path == "/api/setup":
                return self._json(200, app.setup_state())
            if url.path == "/api/setup/installer":
                try:
                    srv = app.backend(parse_qs(url.query).get("server", [""])[0]).server
                    body = installer.build(srv).encode()
                except Exception as e:  # noqa: BLE001
                    return self._send(400, str(e).encode(), "text/plain; charset=utf-8")
                return self._send(200, body, "application/x-sh", {
                    "Content-Disposition": f'attachment; filename="{installer.filename(srv)}"'})
            self._send(404, b"not found", "text/plain")

        def do_POST(self):
            # Eigener Header erzwingt bei fremden Seiten einen CORS-Preflight,
            # den wir nicht beantworten: nur die Steuerseite selbst kann POSTen.
            if not self._host_ok() or self.headers.get("X-Web-Relay") != "1":
                return self._send(403, b"forbidden", "text/plain")
            length = int(self.headers.get("Content-Length") or 0)
            try:
                body = json.loads(self.rfile.read(length) or b"{}")
            except ValueError:
                return self._json(400, {"error": "ungültiges JSON"})
            try:
                result = self._post(self.path, body)
            except (ValueError, LookupError) as e:
                return self._json(400, {"error": str(e)})
            except Exception as e:  # noqa: BLE001
                log.warning("%s: %s", self.path, e)
                return self._json(500, {"error": str(e)})
            if result is None:
                return self._json(404, {"error": "unbekannt"})
            self._json(200, result)

        def _post(self, path: str, body: dict):
            if path == "/api/reload":
                app.active_backend().reload()
                return {"ok": True}
            if path == "/api/switch":
                app.switch(str(body["server_id"]))
                return {"ok": True}
            if path == "/api/site/save":
                app.save_site(body)
                return {"ok": True}
            if path == "/api/connect":
                b = app.active_backend()
                if str(body.get("server_id")) != b.server.id:
                    raise ValueError("Site gehört nicht zum aktiven Server, Seite neu laden")
                site = b.site(int(body["site_id"]))
                if site is None:
                    raise LookupError("Site unbekannt")
                return {"session": app.manager.start(b, site).id}
            if path == "/api/stop":
                app.manager.stop(str(body["session_id"]), "von Hand beendet")
                return {"ok": True}
            if path == "/api/open":
                url = str(body["url"])
                if not url.startswith(("http://", "https://")):
                    raise ValueError("nur http(s)")
                browser.open_url(app.cfg, url)
                return {"ok": True}
            if path == "/api/quit":
                app.quit.set()
                return {"ok": True}
            if path == "/api/setup/save":
                return {"id": app.save_server(body)}
            if path == "/api/setup/profile":
                return {"message": app.save_profile(body)}
            if path == "/api/setup/delete":
                app.delete_server(str(body["id"]))
                return {"ok": True}
            if path == "/api/setup/check":
                return {"items": setup.check(app.backend(body["id"]))}
            if path == "/api/setup/action":
                b = app.backend(body["id"])
                return {"message": setup.run_action(b, str(body["action"]), body.get("data") or {})}
            return None

    return Handler


def serve(app: App) -> ThreadingHTTPServer:
    httpd = ThreadingHTTPServer(("127.0.0.1", app.cfg.control_port), make_handler(app))
    httpd.daemon_threads = True
    threading.Thread(target=httpd.serve_forever, daemon=True, name="web").start()
    return httpd
