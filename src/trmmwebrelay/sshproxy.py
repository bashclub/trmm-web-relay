# SPDX-License-Identifier: GPL-3.0-or-later
"""SSH zu Geräten im Kundennetz über den Tunnel einer offenen Sitzung.

`trmm-web-relay ssh [user@]host` ruft das normale `ssh` auf: eigene
Schlüssel, ssh-agent und ~/.ssh/config gelten. Die Verbindung läuft über
den SOCKS-Verteiler (`trmm-web-relay proxy` als ProxyCommand), die
Host-Schlüssel stehen je Site in einer eigenen known_hosts-Datei, weil
gleiche Adressen bei verschiedenen Kunden verschiedene Geräte sind.
"""

import json
import re
import shlex
import shutil
import socket
import subprocess
import sys
import threading
import urllib.error
import urllib.parse
import urllib.request

from trmmwebrelay import terminal
from trmmwebrelay.config import STATE_DIR, Config
from trmmwebrelay.platform import WINDOWS
from trmmwebrelay.socks import SocksError, connect_via
from trmmwebrelay.targets import parse_targets

KNOWN_HOSTS_DIR = STATE_DIR / "known_hosts.d"  # je Site; known_hosts ist die Datei der Sprung-Hosts
KEEPALIVE = 60  # Sekunden; hält bei offenem Terminal auch den Tunnel aktiv


def parse_destination(dest: str) -> tuple[str, str, int | None]:
    """`[user@]host`, `ssh://[user@]host[:port]` → (user, host, port)."""
    if dest.startswith("ssh://"):
        targets, errors = parse_targets(dest)
        if errors or not targets:
            raise ValueError(errors[0] if errors else f"ungültiges Ziel: {dest}")
        t = targets[0]
        return t.user, t.host, t.port
    user, _, host = dest.rpartition("@")
    if not host or not re.fullmatch(r"[A-Za-z0-9._:-]+", host):
        raise ValueError(f"ungültiges Ziel: {dest}")
    return user, host.strip("[]").lower(), None


def route(cfg: Config, host: str) -> dict:
    """Sitzung, über die der laufende Client host erreicht (site, name)."""
    url = f"http://127.0.0.1:{cfg.control_port}/api/route?host={urllib.parse.quote(host)}"
    req = urllib.request.Request(url, headers={"Host": f"127.0.0.1:{cfg.control_port}"})
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise RuntimeError(f"Keine offene Sitzung erreicht {host}: auf der Steuerseite die Site verbinden") from None
        raise RuntimeError(f"Client antwortet mit HTTP {e.code}") from None
    except OSError:
        raise RuntimeError("Client läuft nicht: zuerst starten und die Site verbinden") from None


def known_hosts(site_key: str):
    KNOWN_HOSTS_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
    return KNOWN_HOSTS_DIR / re.sub(r"[^A-Za-z0-9_.-]", "_", site_key)


def ssh_command(cfg: Config, dest: str, extra: list[str]) -> tuple[list[str], dict]:
    user, host, port = parse_destination(dest)
    info = route(cfg, host)
    exe = shutil.which("ssh")
    if not exe:
        raise RuntimeError("OpenSSH-Client (ssh) nicht gefunden")
    proxy_cmd = terminal.client_command("proxy")
    # OpenSSH für Windows übergibt den ProxyCommand an CreateProcess, sonst an die Shell
    proxy = (subprocess.list2cmdline(proxy_cmd) if WINDOWS else shlex.join(proxy_cmd)) + " %h %p"
    cmd = [
        exe,
        "-o", f"ProxyCommand={proxy}",
        "-o", f"UserKnownHostsFile={known_hosts(info['site'])}",
        "-o", f"ServerAliveInterval={KEEPALIVE}",
        *(["-p", str(port)] if port else []),
        *(["-l", user] if user else []),
        host,
        *extra,
    ]
    return cmd, info


def run_ssh(cfg: Config, dest: str, extra: list[str], wait: bool) -> int:
    """Im Terminal: ssh starten; mit wait bei einem Fehler das Fenster offen halten."""
    try:
        cmd, info = ssh_command(cfg, dest, extra)
        print(f"TRMM Web-Relay: {info['name']} → {dest}", flush=True)
        rc = subprocess.call(cmd)
    except (RuntimeError, ValueError) as e:
        print(f"Fehler: {e}", file=sys.stderr)
        rc = 1
    except KeyboardInterrupt:
        rc = 130
    if wait and rc not in (0, 130):
        try:
            input(f"\nVerbindung beendet (Status {rc}). Enter schließt das Fenster. ")
        except (EOFError, KeyboardInterrupt):
            pass
    return rc


def run_proxy(cfg: Config, host: str, port: int) -> int:
    """ProxyCommand: stdin/stdout mit host:port über den SOCKS-Verteiler verbinden."""
    try:
        sock = connect_via(cfg.socks_port, host, port, timeout=20)
    except SocksError as e:
        print(f"trmm-web-relay proxy: {host}:{port}: {e}", file=sys.stderr)
        return 1
    except OSError as e:
        print(f"trmm-web-relay proxy: SOCKS-Verteiler nicht erreichbar ({e}); läuft der Client?", file=sys.stderr)
        return 1
    sock.settimeout(None)

    def upstream() -> None:
        try:
            while data := sys.stdin.buffer.read1(65536):
                sock.sendall(data)
        except OSError:
            pass
        try:
            sock.shutdown(socket.SHUT_WR)
        except OSError:
            pass

    threading.Thread(target=upstream, daemon=True).start()
    out = sys.stdout.buffer
    try:
        while data := sock.recv(65536):
            out.write(data)
            out.flush()
    except OSError:
        pass
    finally:
        sock.close()
    return 0
