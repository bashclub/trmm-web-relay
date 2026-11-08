# TRMM Web-Relay

[English](README.md)

> Entwicklung: https://code.bashclub.org/bashclub/trmm-web-relay
>
> Handbuch (ohne Anmeldung): https://docs.bashclub.org/s/trmm-web-relay

Weboberflächen in Kundennetzen bei Bedarf öffnen, ohne dauerhafte VPN-Tunnel. Ein Klick auf der lokalen Steuerseite startet über [Tactical RMM](https://github.com/amidaware/tacticalrmm) einen zeitbegrenzten Reverse-SOCKS-Tunnel auf einem Agenten beim Kunden. Ein eigenes Browserprofil öffnet dann die echte Adresse des Ziels, z. B. `https://192.168.1.1`.

- **Nichts dauerhaft offen**: Der Tunnel steht nur während der Sitzung und endet nach Leerlauf (30 min), spätestens nach 4 h oder mit „Beenden“.
- **Kein VPN-Server und keine Portfreigabe beim Kunden**: Der TRMM-Agent baut den Tunnel nach außen zu einem Sprung-Host auf, den der MSP betreibt.
- **Kurzlebige Zertifikate**: Der Client signiert je Sitzung Wegwerf-Schlüssel für 15 Minuten; der Sprung-Host prüft Site, Port und Absender-IP.
- **Nur der Browser**: Ein eigenes Browserprofil geht über einen lokalen SOCKS-Verteiler, der nur die Ziele aktiver Sitzungen durchlässt. Gleiche Adressbereiche bei verschiedenen Kunden stören nicht.
- **Ziele in TRMM**: Websites und bevorzugte Tunnel-Agenten stehen in zwei Benutzerfeldern an der Site, gepflegt in der Steuerseite. Kein zweites Inventar.
- **Mehrere TRMM-Server** je Client, immer einer zur Zeit.

Agenten: Linux und macOS (Windows geplant). Client: Linux, macOS, Windows (Windows und macOS noch wenig erprobt). Sprung-Host: Linux-Server mit Podman ab 4.4.

## Schnellstart

1. **Client installieren** (braucht den OpenSSH-Client und Brave, Chromium, Chrome oder Edge):
   ```sh
   git clone https://code.bashclub.org/bashclub/trmm-web-relay.git
   sh trmm-web-relay/install/client.sh
   ```
   Unter Windows: `powershell -ExecutionPolicy Bypass -File trmm-web-relay\install\client.ps1`
2. **TRMM vorbereiten**: Benutzer und Rolle für den Client anlegen (Rechte `List Clients`, `List Agents`, `View Custom Fields`, `List Scripts`, `Run Scripts`, für die Einrichtung zusätzlich `Manage Custom Fields`, `Manage Scripts`, `Manage Sites`), API-Key für diesen Benutzer erzeugen.
3. **Einrichtung**: Doppelklick auf „TRMM Web-Relay“, Server anlegen, „Prüfen“ und die Schritte abarbeiten (Felder und Skripte in TRMM anlegen, CA erzeugen).
4. **Sprung-Host**: In der Einrichtung den Installer herunterladen und auf einem Linux-Server mit Podman ausführen (`bash trmm-web-relay-sprunghost-*.sh`), TCP 22222 freigeben, Fingerabdruck im Client bestätigen.
5. **Benutzen**: In der Steuerseite bei einer Site „Bearbeiten“, Websites eintragen, „Verbinden“.

Ausführlich: [Schnellstart im Handbuch](https://docs.bashclub.org/s/trmm-web-relay).

## Befehle

```
trmm-web-relay            # Client starten (wie Doppelklick)
trmm-web-relay check      # Einrichtung aller Server prüfen (nur lesend)
trmm-web-relay targets    # Ziele und Tunnel-Agenten aus TRMM anzeigen
trmm-web-relay desktop    # Startsymbol anlegen (--remove: entfernen)
```

Ohne Installation aus dem Repo: `PYTHONPATH=src python3 -m trmmwebrelay`.

## Dokumentation

- Handbuch: https://docs.bashclub.org/s/trmm-web-relay (Quelle: `docs/handbuch/`)
- Entscheidungen: `docs/adr/`
- Sprung-Host im Detail: `docs/sprunghost.md`

## Lizenz und Mitarbeit

GPL-3.0-or-later. Fehler, Fragen und Wünsche als Issue im [Repository](https://code.bashclub.org/bashclub/trmm-web-relay/issues), Beiträge siehe `CONTRIBUTING.md`.

Maintainer: Thorsten Spille, [Spille IT Solutions](https://spille-it.de), bashclub.
