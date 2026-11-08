# SPDX-License-Identifier: GPL-3.0-or-later
"""Zugriff auf die Tactical-RMM-API."""

import json
import urllib.error
import urllib.request


class TrmmError(Exception):
    pass


class Trmm:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self._key = api_key

    def _request(self, method: str, path: str, body=None, timeout: int = 30):
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(
            self.base_url + path,
            method=method,
            data=data,
            headers={
                "X-API-KEY": self._key,
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read()
        except urllib.error.HTTPError as e:
            detail = e.read()[:300].decode(errors="replace")
            raise TrmmError(f"{method} {path}: HTTP {e.code} {detail}") from None
        except urllib.error.URLError as e:
            raise TrmmError(f"{method} {path}: {e.reason}") from None
        return json.loads(raw) if raw else None

    def clients(self) -> list[dict]:
        return self._request("GET", "/clients/")

    def agents(self) -> list[dict]:
        return self._request("GET", "/agents/")

    def custom_fields(self) -> list[dict]:
        return self._request("GET", "/core/customfields/")

    def scripts(self) -> list[dict]:
        return self._request("GET", "/scripts/")

    def run_script(
        self,
        agent_id: str,
        script_id: int,
        args: list[str],
        env_vars: list[str],
        timeout: int,
    ):
        """Startet ein Skript im Modus „nicht warten“ (TRMM: output=forget)."""
        return self._request(
            "POST",
            f"/agents/{agent_id}/runscript/",
            {
                "script": script_id,
                "output": "forget",
                "args": args,
                "env_vars": env_vars,
                "timeout": timeout,
                "run_as_user": False,
            },
        )

    # --- Einrichtung (schreibend, nur nach Bestätigung in der Oberfläche) ---

    def script(self, script_id: int) -> dict:
        return self._request("GET", f"/scripts/{script_id}/")

    def save_script(self, script_id: int | None, data: dict) -> None:
        """Legt ein Skript an (script_id None) oder aktualisiert es. Recht: Manage Scripts."""
        if script_id is None:
            self._request("POST", "/scripts/", data)
        else:
            self._request("PUT", f"/scripts/{script_id}/", data)

    def set_site_fields(self, site_id: int, values: dict[int, str]) -> None:
        """Benutzerfelder einer Site setzen, sonst nichts. Recht: Manage Sites."""
        self._request("PUT", f"/clients/sites/{site_id}/", {
            "site": {},
            "custom_fields": [{"field": fid, "string_value": v} for fid, v in values.items()],
        })

    def may(self, method: str, path: str) -> bool:
        """Prüft ein Recht ohne Änderung: Anfrage an eine Kennung, die es nicht gibt.

        TRMM prüft das Recht vor dem Nachschlagen: 403 heißt kein Recht, 404 heißt erlaubt.
        """
        try:
            self._request(method, path, {})
        except TrmmError as e:
            if "HTTP 403" in str(e):
                return False
            if "HTTP 404" in str(e):
                return True
            raise
        raise TrmmError(f"{method} {path}: unerwartet angenommen")

    def create_site_field(self, name: str) -> None:
        """Textfeld an Sites anlegen. Recht: Manage Custom Fields."""
        self._request("POST", "/core/customfields/", {"model": "site", "type": "text", "name": name})
