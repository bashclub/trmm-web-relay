# ADR 0005: SSH über den Tunnel

Status: angenommen (2026-11-15), erweitert ADR 0001 (nur der Browser)

## Kontext

Viele Geräte im Kundennetz haben keinen TRMM-Agenten und lassen sich nur per SSH verwalten: Switches, Firewalls, NAS, Appliances. Der Tunnel ist ein SOCKS-Proxy und transportiert beliebiges TCP; bis 0.5 nutzte ihn nur das Browserprofil.

Zur Wahl standen:
- ein Terminal im Browser (xterm.js, WebSocket und Pseudo-Terminal im Client, unter Windows zusätzlich pywinpty),
- das normale `ssh` des Rechners in einem lokalen Terminalfenster.

## Entscheidung

- Das normale `ssh` des Rechners, damit eigene Schlüssel, `ssh-agent` und `~/.ssh/config` gelten. Keine neue Abhängigkeit.
- Ziele mit `ssh://[benutzer@]host[:port]` im Feld der Site; ohne Protokoll erkennt der Client SSH an der Kennung des Servers (auf Port 22 nur SSH, auf anderen angegebenen Ports nach HTTPS und HTTP).
- Ein Klick auf ein SSH-Ziel öffnet ein Terminalfenster (Linux: `xdg-terminal-exec`, Terminal des Desktops oder Einstellung `terminal`; macOS: Terminal.app; Windows: neue Konsole) mit `trmm-web-relay ssh`.
- `trmm-web-relay ssh` setzt `trmm-web-relay proxy` als ProxyCommand, eine eigene `known_hosts` je Site (`known_hosts.d/`) und `ServerAliveInterval=60`. Ein offenes Terminal hält die Sitzung damit bis zur Höchstdauer aktiv.
- `trmm-web-relay proxy` steht auch für eigene Aufrufe (`scp`, Ansible) bereit.
- Die Steuerseite öffnet ein Terminal nur für SSH-Ziele einer bereiten Sitzung, geschützt wie die übrigen Aktionen (Header `X-Web-Relay`, nur `127.0.0.1`).

## Folgen

- Die Aussage „nur der Browser“ wird zu „nur Browser und SSH“. Der Verteiler lässt weiter nur Ziele und Netze offener Sitzungen durch; dass jedes lokale Programm ihn nutzen kann, galt schon vorher und steht jetzt im Sicherheitsmodell.
- Wie das Terminal aufgeht, hängt vom System ab; für seltene Terminals gibt es die Einstellung `terminal`.
- Ein Terminal im Browser bleibt möglich (`terminal = "browser"`), wenn Techniker ohne lokales Terminal arbeiten sollen.
