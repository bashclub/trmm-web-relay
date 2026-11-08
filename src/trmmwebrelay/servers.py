# SPDX-License-Identifier: GPL-3.0-or-later
"""Ein Eintrag je TRMM-Server: API-Zugang, geladene Sites, Skript-IDs."""

import logging
import threading
import time

from trmmwebrelay import keystore
from trmmwebrelay.config import Config, Server
from trmmwebrelay.inventory import Site, load_sites
from trmmwebrelay.trmm import Trmm

log = logging.getLogger(__name__)


class Backend:
    def __init__(self, server: Server):
        self.server = server
        self.sites: list[Site] = []
        self.error = ""
        self.loaded_at = 0.0
        self._scripts: dict[str, int] = {}
        self._lock = threading.Lock()

    @property
    def trmm(self) -> Trmm:
        key = keystore.require(self.server.api_key_name, f"TRMM-API-Key für {self.server.name}")
        return Trmm(self.server.trmm_url, key)

    def reload(self) -> None:
        with self._lock:
            try:
                self.sites = load_sites(self.trmm, self.server)
                self._scripts.clear()
                self.error = ""
            except Exception as e:  # noqa: BLE001 - in der Oberfläche zeigen
                self.error = str(e)
                log.warning("%s: %s", self.server.name, e)
            self.loaded_at = time.time()

    def site(self, site_id: int) -> Site | None:
        return next((s for s in self.sites if s.id == site_id), None)

    def script_id(self, name: str) -> int:
        if name not in self._scripts:
            for s in self.trmm.scripts():
                if s.get("name") == name:
                    self._scripts[name] = s["id"]
                    break
            else:
                raise RuntimeError(f"Skript „{name}“ fehlt in TRMM ({self.server.name})")
        return self._scripts[name]


class Registry:
    """Alle Server der Konfiguration; wird bei Änderungen in der Einrichtung neu aufgebaut."""

    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.backends: dict[str, Backend] = {}
        self.sync()

    def sync(self) -> None:
        current = {s.id for s in self.cfg.servers}
        for sid in list(self.backends):
            if sid not in current:
                del self.backends[sid]
        for srv in self.cfg.servers:
            b = self.backends.get(srv.id)
            if b is None:
                self.backends[srv.id] = Backend(srv)
            else:
                b.server = srv

    def get(self, server_id: str) -> Backend | None:
        return self.backends.get(server_id)

    def reload_all(self) -> None:
        threads = [threading.Thread(target=b.reload) for b in self.backends.values()]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
