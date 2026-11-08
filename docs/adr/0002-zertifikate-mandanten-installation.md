# ADR 0002: Zertifikate, mehrere Server, einfache Installation

Status: angenommen (2026-11-06)

## Kontext

Der erste Test mit einem echten Agenten lief (2026-11-06). Danach waren gewünscht:

- Schlüssel in der Weboberfläche erzeugen, bequemes Deployment und Einrichtung,
- ein Client gegen mehrere TRMM-Server, auch für andere MSPs,
- Client und Sprung-Host einfach installierbar, Start per Doppelklick auf dem Desktop (Linux, macOS, Windows).

Mit einem Schlüssel je Site musste jede neue Site über das Deployment des Sprung-Hosts verteilt und der Container neu gestartet werden.

## Entscheidung

- **SSH-Zertifikate statt Schlüsseln je Site.** Der Client hat je Server eine CA im Schlüsselbund. Je Sitzung erzeugt er Wegwerf-Schlüssel und signiert sie für 15 Minuten: Principal `site-<id>` für den Agenten (Konto `wr-tunnel`), `wr-admin` für sich. Der Sprung-Host vertraut nur `TRUSTED_CA`; Port und erlaubte Absender je Site erzeugt er selbst aus TRMM (`AuthorizedPrincipalsCommand`). Neue Sites brauchen am Sprung-Host nichts. Die Kennung im Zertifikat (Site, Agent, Sitzung, Techniker) steht im Log.
- **Mehrere Server**: In der Konfiguration ein `[[server]]` je TRMM mit Sprung-Host; API-Key und CA je Server im Schlüsselbund. Die Steuerseite gruppiert nach Server.
- **Einrichtung in der Weboberfläche**: Server anlegen, Rechte prüfen, Felder und Skripte in TRMM anlegen bzw. aktualisieren (nur nach Rückfrage, der Key braucht dafür zusätzlich `Manage Custom Fields` und `Manage Scripts`), CA erzeugen, Host-Schlüssel des Sprung-Hosts bestätigen (eigene `known_hosts` des Clients), Anmeldung testen.
- **Installation**: Client mit `install/client.sh` bzw. `install/client.ps1` über `uv tool install`, danach Startsymbol (`trmm-web-relay desktop`). Doppelklick startet den Client oder öffnet nur die Steuerseite, wenn er schon läuft. Sprung-Host über einen Installer, den der Client erzeugt: eine Datei mit Image-Quellen, `install.sh` und den öffentlichen Werten; baut das Image mit Podman, legt den TRMM-Key als Secret ab, schreibt Quadlet und startet.

## Ergänzung (2026-11-06)

- **Ein Server zur Zeit**: Die Steuerseite zeigt nur den aktiven Server (`active_server` in der Konfiguration). Umschalten beendet nach Rückfrage alle offenen Verbindungen. So arbeitet man bewusst in einer Instanz und nicht über alle hinweg.
- **Sites bearbeiten**: Websites und Tunnel-Agenten einer Site lassen sich in der Steuerseite pflegen; der Client schreibt nur die beiden Felder (`PUT /clients/sites/<id>/` mit `custom_fields`). Recht `Manage Sites` (schmaler geht es in TRMM nicht). Fehlende Schreibrechte erkennt „Prüfen“ ohne Änderung über Anfragen an nicht vorhandene Kennungen (403 fehlt, 404 erlaubt).
- **Auto-Update des Sprung-Hosts**: Installer richtet einen wöchentlichen Timer ein, der das Image mit aktuellen Paketen neu baut und nur bei Änderungen neu startet.

## Folgen

- Eine Sitzung braucht zwei Zertifikate; wer die CA des Clients hat, kommt an alle Tunnel dieses Servers (wie vorher mit dem Admin-Schlüssel). Sperren eines Technikers: seine CA aus `TRUSTED_CA` nehmen.
- Bestehende Sprung-Hosts mit Schlüsseln je Site müssen auf das neue Image umgestellt werden (`TRUSTED_CA` statt `admin_keys` und `sites/`).
- Windows und macOS sind im Client vorbereitet (Pfade, Startsymbol, Browser), aber noch nicht ausprobiert. Agenten unter Windows brauchen noch ein PowerShell-Tunnel-Skript.
- Später: fertige Pakete ohne Python (AppImage, `.app`, `.exe`) aus der CI, Image in einer Registry.
