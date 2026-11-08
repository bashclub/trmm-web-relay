# SPDX-License-Identifier: GPL-3.0-or-later
"""SOCKS5: Client zum Tunnel und lokaler Verteiler für den Browser.

Der Browser spricht nur mit dem Verteiler (127.0.0.1:<socks_port>). Der
Verteiler leitet eine Verbindung in den Tunnel, wenn das Ziel zu einer aktiven
Sitzung gehört, und direkt ins Internet, wenn der Host freigegeben ist
(Sitzungen haben Vorrang); alles andere wird abgelehnt.
"""

import ipaddress
import logging
import select
import socket
import socketserver
import struct
import threading
from typing import Callable, Protocol

log = logging.getLogger(__name__)


class SocksError(Exception):
    def __init__(self, message: str, code: int = 1):
        super().__init__(message)
        self.code = code


def _recv_exact(sock: socket.socket, n: int) -> bytes:
    buf = b""
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise SocksError("Verbindung vorzeitig geschlossen")
        buf += chunk
    return buf


def _encode_addr(host: str) -> bytes:
    try:
        ip = ipaddress.ip_address(host)
        return (b"\x01" if ip.version == 4 else b"\x04") + ip.packed
    except ValueError:
        name = host.encode("idna")
        return b"\x03" + bytes([len(name)]) + name


def _read_addr(sock: socket.socket) -> tuple[str, int]:
    atyp = _recv_exact(sock, 1)[0]
    if atyp == 1:
        host = str(ipaddress.IPv4Address(_recv_exact(sock, 4)))
    elif atyp == 4:
        host = str(ipaddress.IPv6Address(_recv_exact(sock, 16)))
    elif atyp == 3:
        host = _recv_exact(sock, _recv_exact(sock, 1)[0]).decode("idna")
    else:
        raise SocksError(f"Unbekannter Adresstyp {atyp}", 8)
    (port,) = struct.unpack("!H", _recv_exact(sock, 2))
    return host, port


def connect_via(proxy_port: int, host: str, port: int, timeout: float = 15) -> socket.socket:
    """Baut über den SOCKS5-Proxy auf 127.0.0.1:<proxy_port> eine Verbindung zu host:port auf."""
    s = socket.create_connection(("127.0.0.1", proxy_port), timeout=timeout)
    try:
        s.sendall(b"\x05\x01\x00")
        if _recv_exact(s, 2) != b"\x05\x00":
            raise SocksError("Proxy verlangt Anmeldung")
        s.sendall(b"\x05\x01\x00" + _encode_addr(host) + struct.pack("!H", port))
        rep = _recv_exact(s, 3)
        if rep[1] != 0:
            raise SocksError(f"{host}:{port} nicht erreichbar (SOCKS-Code {rep[1]})", rep[1])
        _read_addr(s)
        return s
    except BaseException:
        s.close()
        raise


def probe(proxy_port: int, timeout: float = 3) -> bool:
    """True, wenn am Port ein SOCKS5-Proxy antwortet (hier: der Tunnel ist bis zum Agenten durch)."""
    try:
        with socket.create_connection(("127.0.0.1", proxy_port), timeout=timeout) as s:
            s.settimeout(timeout)
            s.sendall(b"\x05\x01\x00")
            return _recv_exact(s, 2) == b"\x05\x00"
    except (OSError, SocksError):
        return False


def relay(a: socket.socket, b: socket.socket, on_activity: Callable[[], None]) -> None:
    a.settimeout(None)
    b.settimeout(None)
    peers = {a: b, b: a}
    try:
        while True:
            readable, _, _ = select.select(list(peers), [], [], 60)
            for s in readable:
                data = s.recv(65536)
                if not data:
                    return
                peers[s].sendall(data)
                on_activity()
    except OSError:
        pass
    finally:
        a.close()
        b.close()


class Route(Protocol):
    local_port: int

    def touch(self) -> None: ...


def _reply(sock: socket.socket, code: int) -> None:
    sock.sendall(b"\x05" + bytes([code]) + b"\x00\x01" + b"\x00" * 6)


class _Handler(socketserver.BaseRequestHandler):
    server: "SocksRouter"

    def handle(self) -> None:
        client: socket.socket = self.request
        client.settimeout(30)
        try:
            ver, n = _recv_exact(client, 2)
            methods = _recv_exact(client, n)
            if ver != 5 or 0 not in methods:
                client.sendall(b"\x05\xff")
                return
            client.sendall(b"\x05\x00")
            _, cmd, _ = _recv_exact(client, 3)
            host, port = _read_addr(client)
            if cmd != 1:
                _reply(client, 7)
                return
            route = self.server.resolve(host)
            if route is None:
                if self.server.direct(host, port):
                    self._direct(client, host, port)
                    return
                self.server.rejected(host, port)
                _reply(client, 2)
                return
            try:
                upstream = connect_via(route.local_port, host, port)
            except SocksError as e:
                _reply(client, e.code if 1 <= e.code <= 8 else 1)
                return
            except OSError:
                _reply(client, 1)
                return
            _reply(client, 0)
            route.touch()
            relay(client, upstream, route.touch)
        except (OSError, SocksError):
            pass

    def _direct(self, client: socket.socket, host: str, port: int) -> None:
        """Freigegebener Host: direkt verbinden, zählt nicht als Aktivität einer Sitzung."""
        try:
            upstream = socket.create_connection((host, port), timeout=15)
        except OSError:
            _reply(client, 4)
            return
        _reply(client, 0)
        relay(client, upstream, lambda: None)


class SocksRouter(socketserver.ThreadingTCPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(
        self,
        port: int,
        resolve: Callable[[str], Route | None],
        direct: Callable[[str, int], bool] = lambda host, port: False,
    ):
        super().__init__(("127.0.0.1", port), _Handler)
        self.resolve = resolve
        self.direct = direct
        self._rejected: set[str] = set()
        self._rejected_lock = threading.Lock()

    def rejected(self, host: str, port: int) -> None:
        """Ablehnung loggen, je Ziel nur einmal (hilft beim Pflegen von direct_hosts)."""
        key = f"{host}:{port}"
        with self._rejected_lock:
            if key in self._rejected:
                return
            self._rejected.add(key)
        log.info("abgelehnt (kein Ziel einer Sitzung, nicht in direct_hosts): %s", key)

    def start(self) -> None:
        threading.Thread(target=self.serve_forever, daemon=True, name="socks").start()
