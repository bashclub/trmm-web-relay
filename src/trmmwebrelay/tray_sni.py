# SPDX-License-Identifier: GPL-3.0-or-later
"""Symbol im Infobereich unter Linux: StatusNotifierItem mit DBusMenu.

Spricht D-Bus direkt über jeepney (kommt mit `keyring`), ohne GTK oder Qt.
Angezeigt wird das Symbol von KDE, Cinnamon, XFCE, MATE, Budgie, LXQt und
Ubuntu ohne Zusatz, von GNOME nur mit der Erweiterung „AppIndicator and
KStatusNotifierItem Support“. Fehlt der Infobereich, meldet sich das Symbol
an, sobald er erscheint (z. B. nach dem Einschalten der Erweiterung).
"""

import logging
import os
import threading
from itertools import count

from jeepney import DBusAddress, HeaderFields, MessageType, new_error, new_method_call, new_method_return, new_signal
from jeepney.bus_messages import MatchRule, message_bus
from jeepney.io.blocking import open_dbus_connection
from jeepney.low_level import MessageFlag

from trmmwebrelay.platform import PACKAGE_DIR
from trmmwebrelay.tray import POLL, TITLE, Menu

log = logging.getLogger(__name__)

WATCHER = "org.kde.StatusNotifierWatcher"
ITEM_PATH, ITEM_IFACE = "/StatusNotifierItem", "org.kde.StatusNotifierItem"
MENU_PATH, MENU_IFACE = "/MenuBar", "com.canonical.dbusmenu"
PROPS = "org.freedesktop.DBus.Properties"
ICON_SVG = PACKAGE_DIR / "static" / "icon.svg"

_INTROSPECT = {
    ITEM_PATH: f"""<node><interface name="{ITEM_IFACE}">
<property name="Category" type="s" access="read"/><property name="Id" type="s" access="read"/>
<property name="Title" type="s" access="read"/><property name="Status" type="s" access="read"/>
<property name="WindowId" type="i" access="read"/><property name="IconName" type="s" access="read"/>
<property name="IconThemePath" type="s" access="read"/><property name="IconPixmap" type="a(iiay)" access="read"/>
<property name="ToolTip" type="(sa(iiay)ss)" access="read"/><property name="ItemIsMenu" type="b" access="read"/>
<property name="Menu" type="o" access="read"/>
<method name="Activate"><arg type="i" direction="in"/><arg type="i" direction="in"/></method>
<method name="SecondaryActivate"><arg type="i" direction="in"/><arg type="i" direction="in"/></method>
<method name="ContextMenu"><arg type="i" direction="in"/><arg type="i" direction="in"/></method>
<method name="Scroll"><arg type="i" direction="in"/><arg type="s" direction="in"/></method>
<signal name="NewToolTip"/><signal name="NewStatus"><arg type="s"/></signal>
</interface></node>""",
    MENU_PATH: f"""<node><interface name="{MENU_IFACE}">
<property name="Version" type="u" access="read"/><property name="TextDirection" type="s" access="read"/>
<property name="Status" type="s" access="read"/><property name="IconThemePath" type="as" access="read"/>
<method name="GetLayout"><arg type="i" direction="in"/><arg type="i" direction="in"/><arg type="as" direction="in"/>
<arg type="u" direction="out"/><arg type="(ia{{sv}}av)" direction="out"/></method>
<method name="GetGroupProperties"><arg type="ai" direction="in"/><arg type="as" direction="in"/>
<arg type="a(ia{{sv}})" direction="out"/></method>
<method name="GetProperty"><arg type="i" direction="in"/><arg type="s" direction="in"/><arg type="v" direction="out"/></method>
<method name="Event"><arg type="i" direction="in"/><arg type="s" direction="in"/><arg type="v" direction="in"/>
<arg type="u" direction="in"/></method>
<method name="EventGroup"><arg type="a(isvu)" direction="in"/><arg type="ai" direction="out"/></method>
<method name="AboutToShow"><arg type="i" direction="in"/><arg type="b" direction="out"/></method>
<method name="AboutToShowGroup"><arg type="ai" direction="in"/><arg type="ai" direction="out"/>
<arg type="ai" direction="out"/></method>
<signal name="LayoutUpdated"><arg type="u"/><arg type="i"/></signal>
</interface></node>""",
}


def start(menu: Menu) -> None:
    """Symbol in einem eigenen Thread; Fehler bleiben im Log."""
    threading.Thread(target=_run, args=(menu,), daemon=True, name="tray").start()


def _run(menu: Menu) -> None:
    try:
        Tray(menu).loop()
    except Exception as e:  # noqa: BLE001 - ohne Infobereich weiterlaufen
        log.warning("Symbol im Infobereich fehlgeschlagen: %s", e)


class Tray:
    def __init__(self, menu: Menu):
        self.menu = menu
        self.conn = open_dbus_connection(bus="SESSION")
        self.name = f"org.kde.StatusNotifierItem-{os.getpid()}-1"
        self.conn.send_and_get_reply(message_bus.RequestName(self.name), timeout=5)
        rule = MatchRule(type="signal", sender="org.freedesktop.DBus", interface="org.freedesktop.DBus",
                         member="NameOwnerChanged", path="/org/freedesktop/DBus")
        rule.add_arg_condition(0, WATCHER)
        self.conn.send_and_get_reply(message_bus.AddMatch(rule), timeout=5)
        self.revision = 1
        self.items = menu.items()
        self.ids = {i + 1: it for i, it in enumerate(self.items)}
        self.register_serial = 0
        self.warned = False

    # --- Ablauf ----------------------------------------------------------

    def loop(self) -> None:
        self._register()
        while not self.menu.app.quit.is_set():
            try:
                msg = self.conn.receive(timeout=POLL)
            except TimeoutError:
                msg = None
            if msg is not None:
                self._handle(msg)
            self._refresh()
        self.conn.close()

    def _send(self, msg) -> int:
        serial = next(self._serials)
        self.conn.send(msg, serial=serial)
        return serial

    @property
    def _serials(self) -> count:
        return self.conn.outgoing_serial

    def _register(self) -> None:
        watcher = DBusAddress("/StatusNotifierWatcher", bus_name=WATCHER, interface=WATCHER)
        self.register_serial = self._send(
            new_method_call(watcher, "RegisterStatusNotifierItem", "s", (self.name,)))

    def _refresh(self) -> None:
        items = self.menu.items()
        if items == self.items:
            return
        self.items = items
        self.ids = {i + 1: it for i, it in enumerate(items)}
        self.revision += 1
        self._send(new_signal(DBusAddress(MENU_PATH, interface=MENU_IFACE), "LayoutUpdated", "ui",
                              (self.revision, 0)))
        self._send(new_signal(DBusAddress(ITEM_PATH, interface=ITEM_IFACE), "NewToolTip"))

    def _handle(self, msg) -> None:
        h = msg.header
        if h.message_type == MessageType.error and h.fields.get(HeaderFields.reply_serial) == self.register_serial:
            if not self.warned:
                self.warned = True
                log.info("Kein Infobereich gefunden (%s). Unter GNOME die Erweiterung „AppIndicator and "
                         "KStatusNotifierItem Support“ einschalten; das Symbol erscheint dann von selbst.",
                         msg.body[0] if msg.body else h.fields.get(HeaderFields.error_name))
            return
        if h.message_type == MessageType.method_return and h.fields.get(HeaderFields.reply_serial) == self.register_serial:
            log.info("Symbol im Infobereich angemeldet")
            self.warned = False
            return
        if h.message_type == MessageType.signal:
            # NameOwnerChanged(name, alt, neu): Infobereich (neu) gestartet
            if h.fields.get(HeaderFields.member) == "NameOwnerChanged" and msg.body[0] == WATCHER and msg.body[2]:
                self._register()
            return
        if h.message_type != MessageType.method_call:
            return
        try:
            reply = self._call(msg)
        except KeyError as e:
            reply = new_error(msg, "org.freedesktop.DBus.Error.UnknownMethod", "s", (f"unbekannt: {e}",))
        except Exception as e:  # noqa: BLE001
            reply = new_error(msg, "org.freedesktop.DBus.Error.Failed", "s", (str(e),))
        if not h.flags & MessageFlag.no_reply_expected:
            self._send(reply)

    # --- Methoden --------------------------------------------------------

    def _call(self, msg):
        f = msg.header.fields
        path, iface, member = f.get(HeaderFields.path), f.get(HeaderFields.interface), f[HeaderFields.member]
        body = msg.body
        if member == "Introspect":
            return new_method_return(msg, "s", (_INTROSPECT.get(path, "<node/>"),))
        if iface == PROPS or (iface is None and member in ("Get", "GetAll")):
            props = self._item_props() if path == ITEM_PATH else self._menu_props() if path == MENU_PATH else {}
            if member == "GetAll":
                return new_method_return(msg, "a{sv}", (props,))
            if member == "Get":
                if body[1] not in props:
                    return new_error(msg, "org.freedesktop.DBus.Error.UnknownProperty", "s", (body[1],))
                return new_method_return(msg, "v", (props[body[1]],))
            return new_error(msg, "org.freedesktop.DBus.Error.PropertyReadOnly", "s", ("nur lesbar",))
        if path == ITEM_PATH:
            if member in ("Activate", "SecondaryActivate"):
                self.menu.activate("open")
            elif member not in ("ContextMenu", "Scroll"):
                raise KeyError(member)
            return new_method_return(msg)
        if path == MENU_PATH:
            return self._menu_call(msg, member, body)
        raise KeyError(f"{path} {member}")

    def _menu_call(self, msg, member, body):
        if member == "GetLayout":
            parent = body[0]
            if parent == 0:
                children = [("(ia{sv}av)", (i, self._entry(it), [])) for i, it in self.ids.items()]
                layout = (0, {"children-display": ("s", "submenu")}, children)
            else:
                layout = (parent, self._entry(self.ids[parent]), [])
            return new_method_return(msg, "u(ia{sv}av)", (self.revision, layout))
        if member == "GetGroupProperties":
            ids = body[0] or list(self.ids)
            return new_method_return(msg, "a(ia{sv})", ([(i, self._entry(self.ids[i])) for i in ids if i in self.ids],))
        if member == "GetProperty":
            props = self._entry(self.ids[body[0]])
            if body[1] not in props:
                return new_error(msg, "org.freedesktop.DBus.Error.InvalidArgs", "s", (body[1],))
            return new_method_return(msg, "v", (props[body[1]],))
        if member == "Event":
            self._event(body[0], body[1])
            return new_method_return(msg)
        if member == "EventGroup":
            for item_id, event, _data, _ts in body[0]:
                self._event(item_id, event)
            return new_method_return(msg, "ai", ([],))
        if member == "AboutToShow":
            return new_method_return(msg, "b", (False,))
        if member == "AboutToShowGroup":
            return new_method_return(msg, "aiai", ([], []))
        raise KeyError(member)

    def _event(self, item_id: int, event: str) -> None:
        it = self.ids.get(item_id)
        if event == "clicked" and it and it.enabled:
            self.menu.activate(it.key)

    # --- Eigenschaften ---------------------------------------------------

    @staticmethod
    def _entry(it) -> dict:
        if not it.key:
            return {"type": ("s", "separator")}
        props = {"label": ("s", it.label)}
        if not it.enabled:
            props["enabled"] = ("b", False)
        return props

    def _item_props(self) -> dict:
        tooltip = f"{TITLE}: {self.menu.status()}"
        return {
            "Category": ("s", "ApplicationStatus"),
            "Id": ("s", "trmm-web-relay"),
            "Title": ("s", TITLE),
            "Status": ("s", "Active"),
            "WindowId": ("i", 0),
            # Absoluter Pfad: GNOME (AppIndicator), KDE und XFCE laden die Datei direkt
            "IconName": ("s", str(ICON_SVG)),
            "IconThemePath": ("s", str(ICON_SVG.parent)),
            "IconPixmap": ("a(iiay)", []),
            "AttentionIconName": ("s", ""),
            "OverlayIconName": ("s", ""),
            "ToolTip": ("(sa(iiay)ss)", ("", [], TITLE, tooltip)),
            "ItemIsMenu": ("b", True),
            "Menu": ("o", MENU_PATH),
        }

    @staticmethod
    def _menu_props() -> dict:
        return {
            "Version": ("u", 3),
            "TextDirection": ("s", "ltr"),
            "Status": ("s", "normal"),
            "IconThemePath": ("as", []),
        }
