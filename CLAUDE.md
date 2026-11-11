# TRMM Web-Relay: Projektkontext

Name: **TRMM Web-Relay** (Befehl `trmm-web-relay`, Paket `trmmwebrelay`). Lokaler Client, mit dem MSPs Weboberflächen in Kundennetzen in **einem Schritt** im normalen Browser öffnen, ohne dauerhafte VPN-Tunnel: Tactical RMM startet auf einem Agenten der Site einen zeitbegrenzten Reverse-SOCKS-Tunnel zu einem Sprung-Host, der Client öffnet die Ziele in einem eigenen Browserprofil. Entwurf: `docs/adr/`. Handbuch: `docs/handbuch/` (wird nach Outline veröffentlicht, Regeln in `docs/handbuch/README.md`).

Repository: https://code.bashclub.org/bashclub/trmm-web-relay. Lizenz GPL-3.0-or-later, Commits mit `Signed-off-by` (`CONTRIBUTING.md`).

## Arbeitsregeln

- Doku, Commits und Kommentare auf Deutsch, Bezeichner auf Englisch. Neue Dateien beginnen mit `SPDX-License-Identifier: GPL-3.0-or-later`.
- Erst Plan und Struktur vorschlagen, dann bauen. Architekturfragen klärt der Maintainer.
- **Kein Geheimnis im Repo**, auch nicht verschlüsselt. Geheimnisse (TRMM-API-Key, CA) im Schlüsselbund des Systems, ohne Schlüsselbund in `~/.local/share/trmm-web-relay/secrets/`. Geheimnisse nie auf den Bildschirm ausgeben, nur per Pipe/stdin weitergeben.
- **Nichts Internes im Repo**: keine Kundennamen, eigenen Hostnamen, Netze oder Fingerabdrücke; Beispiele mit `example.com` und Dokumentationsnetzen (`203.0.113.0/24`, `192.168.1.0/24`). Interne Notizen gehören in `CLAUDE.local.md` (nicht versioniert).
- **Produktive Systeme nicht anfassen**: TRMM und Kundengeräte sind produktiv. Lesende API-Aufrufe sind in Ordnung; Skripte auf Kundengeräten und Schreiben in TRMM nur nach ausdrücklicher Freigabe.
- Das Werkzeug ist allgemein für MSPs: keine Voreinstellungen für einen bestimmten MSP im Code.
- Änderungen an Verhalten, Einstellungen, Befehlen oder Meldungen ziehen das Handbuch im selben Commit nach (`tests/handbuch.sh` prüft Referenz und Aufbereitung).

## Aufbau

- `src/trmmwebrelay/`: Client (Python ab 3.11, Standardbibliothek plus `keyring`; für das Symbol im Infobereich jeepney unter Linux, pystray/Pillow unter Windows und macOS, ADR 0004), Steuerseite und Einrichtung als statische Seiten in `static/`.
- `trmm-scripts/`: Skripte „Web-Relay: Tunnel starten/stoppen“ für Agenten (Linux, macOS); die Einrichtung legt sie in TRMM an.
- `jumphost/`: Image (nur sshd) und `install.sh` des Sprung-Hosts; der Client packt beides in einen Installer.
- `install/`: Installer des Clients (`uv tool install`).
- `docs/`: ADRs, Beschreibung des Sprung-Hosts, Handbuch.

## Offen

- PowerShell-Tunnel-Skript für Windows-Agenten.
- Fertige Pakete ohne Python (AppImage, `.app`, `.exe`), Image in einer Registry.
- Windows- und macOS-Client ausprobieren.
- Englische Fassung des Handbuchs.
