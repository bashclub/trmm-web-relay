# SPDX-License-Identifier: GPL-3.0-or-later
"""Erkennen, was hinter host:port steckt: http oder https, Seitentitel."""

import html
import json
import re
import ssl
import threading
from dataclasses import asdict, dataclass
from urllib.parse import urljoin, urlsplit

from trmmwebrelay.config import CACHE_DIR
from trmmwebrelay.socks import SocksError, connect_via
from trmmwebrelay.targets import Target, is_ip, make_url

CACHE_FILE = CACHE_DIR / "erkannt.json"
_cache_lock = threading.Lock()


@dataclass
class Detected:
    url: str
    title: str
    error: str = ""


def _tls_context() -> ssl.SSLContext:
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    # Alte Appliances sprechen oft nur alte TLS-Versionen
    ctx.minimum_version = ssl.TLSVersion.MINIMUM_SUPPORTED
    try:
        ctx.set_ciphers("DEFAULT:@SECLEVEL=0")
    except ssl.SSLError:
        pass
    return ctx


def _open(proxy_port: int, scheme: str, host: str, port: int):
    sock = connect_via(proxy_port, host, port, timeout=8)
    if scheme == "https":
        sock.settimeout(6)
        try:
            return _tls_context().wrap_socket(sock, server_hostname=None if is_ip(host) else host)
        except BaseException:
            sock.close()
            raise
    return sock


def _get(proxy_port: int, scheme: str, host: str, port: int, path: str) -> tuple[int, dict, str]:
    sock = _open(proxy_port, scheme, host, port)
    try:
        sock.settimeout(6)
        default = 443 if scheme == "https" else 80
        h = f"[{host}]" if ":" in host else host
        hosthdr = h if port == default else f"{h}:{port}"
        sock.sendall(
            (
                f"GET {path} HTTP/1.1\r\nHost: {hosthdr}\r\nUser-Agent: trmm-web-relay\r\n"
                "Accept: text/html,*/*\r\nConnection: close\r\n\r\n"
            ).encode()
        )
        data = b""
        try:
            while len(data) < 256 * 1024:
                chunk = sock.recv(65536)
                if not chunk:
                    break
                data += chunk
                if b"</title>" in data.lower():
                    break
        except (TimeoutError, ssl.SSLError, OSError):
            if not data:
                raise
    finally:
        sock.close()
    head, _, body = data.partition(b"\r\n\r\n")
    lines = head.decode("iso-8859-1").split("\r\n")
    m = re.match(r"HTTP/\d(?:\.\d)?\s+(\d{3})", lines[0] if lines else "")
    if not m:
        raise SocksError("keine HTTP-Antwort")
    headers = {}
    for line in lines[1:]:
        k, _, v = line.partition(":")
        headers[k.strip().lower()] = v.strip()
    return int(m.group(1)), headers, body.decode("utf-8", errors="replace")


def _title(body: str) -> str:
    m = re.search(r"<title[^>]*>(.*?)</title>", body, re.I | re.S)
    if not m:
        return ""
    return re.sub(r"\s+", " ", html.unescape(m.group(1))).strip()[:80]


def _fetch_title(proxy_port: int, scheme: str, host: str, port: int, path: str) -> str:
    """Seitentitel, folgt bis zu drei Weiterleitungen auf demselben Host."""
    for _ in range(4):
        status, headers, body = _get(proxy_port, scheme, host, port, path)
        loc = headers.get("location")
        if 300 <= status < 400 and loc:
            nxt = urlsplit(urljoin(make_url(scheme, host, port, path), loc))
            if (nxt.hostname or "").lower() != host or nxt.scheme not in ("http", "https"):
                return ""
            scheme = nxt.scheme
            port = nxt.port or (443 if scheme == "https" else 80)
            path = (nxt.path or "/") + (f"?{nxt.query}" if nxt.query else "")
            continue
        return _title(body)
    return ""


def detect(proxy_port: int, target: Target) -> Detected:
    if target.scheme:
        candidates = [(target.scheme, target.port or (443 if target.scheme == "https" else 80))]
    elif target.port:
        candidates = [("https", target.port), ("http", target.port)]
    else:
        candidates = [("https", 443), ("http", 80)]

    last_error = ""
    for scheme, port in candidates:
        try:
            title = _fetch_title(proxy_port, scheme, target.host, port, target.path)
        except SocksError as e:
            if e.code in (3, 4, 5):  # Netz/Host nicht erreichbar, Verbindung abgelehnt
                last_error = str(e)
                if target.port or target.scheme:
                    break  # anderes Protokoll auf demselben Port hilft nicht
                continue
            last_error = str(e)
            continue
        except (ssl.SSLError, TimeoutError, OSError) as e:
            last_error = f"{scheme}: {e.__class__.__name__}"
            continue
        return Detected(url=target.url(scheme, port), title=title)
    return Detected(url=target.url(), title="", error=last_error or "nicht erreichbar")


def load_cache() -> dict[str, Detected]:
    try:
        data = json.loads(CACHE_FILE.read_text())
        return {k: Detected(**v) for k, v in data.items()}
    except (OSError, ValueError, TypeError):
        return {}


def save_cache(key: str, value: Detected) -> None:
    with _cache_lock:
        data = {k: asdict(v) for k, v in load_cache().items()}
        data[key] = asdict(value)
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        CACHE_FILE.write_text(json.dumps(data, indent=1, ensure_ascii=False))
