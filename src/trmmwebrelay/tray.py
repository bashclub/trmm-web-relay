# SPDX-License-Identifier: GPL-3.0-or-later
"""Symbol im Infobereich (Tray), solange der Client läuft.

Menü: Steuerseite, Einrichtung, Zahl der offenen Sitzungen, alle Sitzungen
beenden, Client beenden. Linux: StatusNotifierItem über D-Bus (`tray_sni`,
mit jeepney, das `keyring` ohnehin mitbringt). Windows und macOS: pystray.
Gibt es keinen Infobereich, läuft der Client ohne Symbol weiter.
"""

import logging
import threading
from dataclasses import dataclass

from trmmwebrelay import browser
from trmmwebrelay.platform import MACOS, PACKAGE_DIR, WINDOWS

log = logging.getLogger(__name__)
TITLE = "TRMM Web-Relay"
ICON_PNG = PACKAGE_DIR / "static" / "icon.png"
POLL = 2.0  # Sekunden zwischen zwei Blicken auf die Sitzungen


@dataclass(frozen=True)
class Item:
    key: str  # "" = Trennlinie
    label: str = ""
    enabled: bool = True


SEPARATOR = Item("")


class Menu:
    """Menüeinträge und Aktionen, gemeinsam für alle Umsetzungen."""

    def __init__(self, app):
        self.app = app
        self.url = f"http://127.0.0.1:{app.cfg.control_port}/"

    def count(self) -> int:
        return sum(1 for s in list(self.app.manager.sessions.values()) if s.active)

    def status(self) -> str:
        n = self.count()
        if n == 0:
            return "Keine offene Sitzung"
        return "1 offene Sitzung" if n == 1 else f"{n} offene Sitzungen"

    def items(self) -> list[Item]:
        n = self.count()
        return [
            Item("open", "Steuerseite öffnen"),
            Item("setup", "Einrichtung"),
            SEPARATOR,
            Item("status", self.status(), enabled=False),
            Item("stop", "Alle Sitzungen beenden", enabled=n > 0),
            SEPARATOR,
            Item("quit", "Beenden" if n == 0 else f"Beenden ({n} Sitzung{'en' if n > 1 else ''} schließen)"),
        ]

    def activate(self, key: str) -> None:
        """Aktion im eigenen Thread, damit das Menü nicht hängt."""
        actions = {
            "open": lambda: self._open("" if self.app.cfg.servers else "einrichtung"),
            "setup": lambda: self._open("einrichtung"),
            "stop": lambda: self.app.manager.stop_all("im Infobereich beendet"),
            "quit": self.app.quit.set,
        }
        if key in actions:
            threading.Thread(target=actions[key], daemon=True, name=f"tray-{key}").start()

    def _open(self, path: str) -> None:
        try:
            browser.open_url(self.app.cfg, self.url + path + "?profil")
        except RuntimeError as e:
            log.error("%s", e)


def run(app) -> None:
    """Blockiert, bis der Client beendet werden soll (app.quit)."""
    menu = Menu(app)
    if WINDOWS or MACOS:
        if _run_pystray(menu):
            return
    elif tray_sni is None:
        log.info("Kein Symbol im Infobereich (%s)", _sni_error)
    else:
        tray_sni.start(menu)
    _wait(app)


def _wait(app) -> None:
    try:
        while not app.quit.wait(1):
            pass
    except KeyboardInterrupt:
        pass


def _run_pystray(menu: Menu) -> bool:
    """Windows/macOS: pystray im Haupt-Thread (macOS verlangt das)."""
    try:
        import pystray
        from PIL import Image
    except ImportError as e:
        log.info("Kein Symbol im Infobereich (%s)", e)
        return False

    def entry(it: Item):
        if not it.key:
            return pystray.Menu.SEPARATOR
        return pystray.MenuItem(
            lambda _i, k=it.key: _label(menu, k),
            lambda _icon, _i, k=it.key: menu.activate(k),
            enabled=lambda _i, k=it.key: _enabled(menu, k),
            default=it.key == "open",
        )

    icon = pystray.Icon("trmm-web-relay", Image.open(ICON_PNG), TITLE,
                        pystray.Menu(*(entry(it) for it in menu.items())))

    def watch() -> None:
        last = None
        while not menu.app.quit.wait(POLL):
            now = menu.count()
            if now != last:
                last = now
                icon.title = f"{TITLE}: {menu.status()}"
                icon.update_menu()
        icon.stop()

    threading.Thread(target=watch, daemon=True, name="tray-watch").start()
    try:
        icon.run()
    except KeyboardInterrupt:
        menu.app.quit.set()
    except Exception as e:  # noqa: BLE001 - ohne Infobereich weiterlaufen
        log.warning("Symbol im Infobereich fehlgeschlagen: %s", e)
        return False
    return True


def _label(menu: Menu, key: str) -> str:
    return next(it.label for it in menu.items() if it.key == key)


def _enabled(menu: Menu, key: str) -> bool:
    return next(it.enabled for it in menu.items() if it.key == key)


# Linux: jeepney schon beim Laden des Moduls importieren, solange nur ein
# Thread läuft. Später importiert, kollidiert es mit keyring, das jeepney im
# Lade-Thread importiert (Deadlock beim Modul-Import).
tray_sni = None
_sni_error: Exception | None = None
if not (WINDOWS or MACOS):
    try:
        from trmmwebrelay import tray_sni
    except Exception as e:  # noqa: BLE001 - ohne Infobereich weiterlaufen
        _sni_error = e
