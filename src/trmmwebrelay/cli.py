# SPDX-License-Identifier: GPL-3.0-or-later
"""TRMM Web-Relay: Weboberflächen in Kundennetzen über Tactical RMM öffnen.

Ohne Befehl: Client starten (bzw. die Steuerseite öffnen, wenn er schon läuft).
"""

import argparse
import json
import logging
import logging.handlers
import signal
import sys
import threading
import urllib.request

from trmmwebrelay import browser, desktop, setup, version
from trmmwebrelay.config import CONFIG_PATH, STATE_DIR, Config, load
from trmmwebrelay.inventory import Agent, choose_agent
from trmmwebrelay.servers import Registry
from trmmwebrelay.session import SessionManager
from trmmwebrelay.socks import SocksRouter
from trmmwebrelay.trmm import TrmmError
from trmmwebrelay.web import APP_ID, App, serve

log = logging.getLogger("trmmwebrelay")


def _running(cfg: Config) -> bool:
    """Läuft schon ein Client auf dem Steuerport?"""
    req = urllib.request.Request(
        f"http://127.0.0.1:{cfg.control_port}/api/ping",
        headers={"Host": f"127.0.0.1:{cfg.control_port}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=2) as r:
            return json.load(r).get("app") == APP_ID
    except Exception:  # noqa: BLE001
        return False


def cmd_serve(cfg: Config, args) -> None:
    url = f"http://127.0.0.1:{cfg.control_port}/"
    start_page = url if cfg.servers else url + "einrichtung"
    if _running(cfg):
        log.info("Client läuft schon, öffne die Steuerseite")
        if not args.no_browser:
            browser.open_url(cfg, start_page + "?profil")
        return

    registry = Registry(cfg)
    manager = SessionManager(cfg, registry)
    app = App(cfg, registry, manager)
    if cfg.active:
        threading.Thread(target=registry.get(cfg.active.id).reload, daemon=True).start()
    router = SocksRouter(
        cfg.socks_port, manager.resolve, lambda host, port: browser.direct_allowed(cfg, host, port)
    )
    router.start()
    version.check_in_background(cfg)
    serve(app)
    log.info("Steuerseite: %s", url)
    log.info("SOCKS-Verteiler: 127.0.0.1:%s", cfg.socks_port)
    if not args.no_browser:
        try:
            browser.open_url(cfg, start_page + "?profil")
        except RuntimeError as e:
            log.error("%s", e)

    signal.signal(signal.SIGTERM, lambda *_: app.quit.set())
    try:
        while not app.quit.wait(1):
            pass
    except KeyboardInterrupt:
        pass
    log.info("Beende offene Sitzungen …")
    manager.stop_all("Client beendet")


def cmd_targets(cfg: Config, args) -> None:
    registry = Registry(cfg)
    for b in registry.backends.values():
        b.reload()
        print(f"== {b.server.name} ({b.server.trmm_url})")
        if b.error:
            print(f"  ! {b.error}")
            continue
        agents = [Agent.from_api(a) for a in b.trmm.agents()]
        for s in b.sites:
            if not s.targets and not s.target_errors and not args.all:
                continue
            agent, notes = choose_agent(s, agents)
            print(f"{s.client} / {s.name} (Site {s.id})")
            print(f"  Tunnel-Agent: {agent.hostname if agent else '–'}"
                  + (f"  [{'; '.join(notes)}]" if notes else ""))
            for t in s.targets:
                how = t.scheme or "automatisch"
                print(f"  - {t.name or '(Name aus Seitentitel)'}: {t.host}"
                      f"{':' + str(t.port) if t.port else ''}{t.path if t.path != '/' else ''} [{how}]")
            for e in s.target_errors:
                print(f"  ! {e}")


def cmd_check(cfg: Config, args) -> None:
    ok = True
    print(f"Konfiguration: {CONFIG_PATH}" + ("" if CONFIG_PATH.exists() else " (fehlt)"))
    if not cfg.servers:
        print("FEHLT Kein Server eingerichtet (Client starten, Einrichtung öffnet sich)")
        ok = False
    registry = Registry(cfg)
    for b in registry.backends.values():
        print(f"== {b.server.name}")
        for it in setup.check(b):
            ok &= it["state"] in ("ok", "info")
            mark = {"ok": "ok   ", "fehlt": "FEHLT", "fehler": "FEHLER", "info": "info "}.get(it["state"], it["state"])
            print(f"{mark} {it['title']}" + (f": {it['detail']}" if it["detail"] and it["state"] != "ok" else ""))
    exe = browser.find(cfg)
    ok &= bool(exe)
    print(("ok    " if exe else "FEHLT ") + f"Browser: {exe or 'Brave/Chromium nicht gefunden'}")
    installed, newest = version.current(), version.latest(cfg)
    if version.is_newer(newest, installed):
        print(f"info  Version {installed}: neue Version {newest} verfügbar (Handbuch: Updates)")
    else:
        print(f"ok    Version {installed}" + ("" if newest else " (neueste Version nicht abgefragt)"))
    sys.exit(0 if ok else 1)


def cmd_desktop(cfg: Config, args) -> None:
    if args.remove:
        for p in desktop.uninstall():
            print(f"entfernt: {p}")
        return
    for p in desktop.install():
        print(f"angelegt: {p}")


def main() -> None:
    parser = argparse.ArgumentParser(prog="trmm-web-relay", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("--version", action="version", version=f"%(prog)s {version.current()}")
    sub = parser.add_subparsers(dest="cmd")
    p = sub.add_parser("serve", help="Client starten (Standard)")
    p.add_argument("--no-browser", action="store_true", help="Steuerseite nicht im Browser öffnen")
    p = sub.add_parser("targets", help="Ziele und Tunnel-Agenten aus TRMM anzeigen")
    p.add_argument("--all", action="store_true", help="auch Sites ohne Ziele")
    sub.add_parser("check", help="Einrichtung prüfen (nur lesend)")
    p = sub.add_parser("desktop", help="Startsymbol auf Desktop und im Startmenü anlegen")
    p.add_argument("--remove", action="store_true", help="Startsymbol entfernen")
    args = parser.parse_args()
    if args.cmd is None:
        args.cmd, args.no_browser = "serve", False

    handlers = []
    if sys.stderr is not None and sys.stderr.isatty():
        handlers.append(logging.StreamHandler())
    if args.cmd == "serve":
        # Beim Start per Doppelklick gibt es kein Terminal: Protokoll in eine Datei
        STATE_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
        handlers.append(logging.handlers.RotatingFileHandler(
            STATE_DIR / "client.log", maxBytes=1_000_000, backupCount=2, encoding="utf-8"))
    elif not handlers:
        handlers.append(logging.StreamHandler())
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s", handlers=handlers)
    try:
        cfg = load()
        {"serve": cmd_serve, "targets": cmd_targets, "check": cmd_check,
         "desktop": cmd_desktop}[args.cmd](cfg, args)
    except (RuntimeError, TrmmError, ValueError, OSError) as e:
        log.error("%s", e)
        if sys.stderr is not None:
            print(f"Fehler: {e}", file=sys.stderr)
        sys.exit(1)
