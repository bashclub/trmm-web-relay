---
title: Installer des Sprung-Hosts
audience: Admin
outline:
outline_id:
---
Der Installer `trmm-web-relay-sprunghost-<server>.sh` kommt aus der Einrichtung des Clients. Er enthält die Quellen des Images und `install.sh`, dazu als Vorgabe TRMM-Adresse, CA und Port des Servers. Er läuft auf Linux mit Podman ab 4.4, als root oder als eigener Dienstbenutzer.

```
bash trmm-web-relay-sprunghost-<server>.sh [--no-start | --update | --uninstall | --help]
```

## Optionen
| Option | Bedeutung |
|---|---|
| ohne | installieren bzw. aktualisieren und starten |
| `--no-start` | nur Dateien schreiben und Image bauen, nicht starten |
| `--update` | Image ohne Cache mit aktuellen Paketen neu bauen, nur bei geänderten Paketen umtaggen und neu starten (ruft der Timer auf) |
| `--uninstall` | Dienst, Timer, Image, Secret und Quellen entfernen; Einstellungen und Volume mit Host-Schlüssel bleiben |
| `--help` | Werte und Optionen anzeigen |

## Variablen
Jede Variable kann man in der Umgebung vorgeben; sonst fragt der Installer (im Terminal) oder nimmt den vorhandenen Wert aus `jumphost.env`.

| Variable | Standard | Bedeutung |
|---|---|---|
| `TRMM_URL` | aus dem Client | TRMM-API, muss mit `https://` beginnen |
| `TRUSTED_CA` | aus dem Client | CA, die hinzukommt; vorhandene CAs bleiben |
| `PUBLIC_PORT` | `22222` | Port auf dem Server |
| `ADMIN_FROM` | Abfrage beim ersten Mal | IPv4-Netze der Techniker, leer: überall |
| `ALLOW_FROM` | leer | feste IPv4-Netze für alle Sites |
| `TRMM_API_KEY` | Abfrage, wenn kein Secret existiert | TRMM-Key nur zum Lesen; gesetzt ersetzt er das vorhandene Secret |
| `AUTO_UPDATE` | `1` | `1`: wöchentlicher Timer für das Auto-Update, `0`: kein Timer (ein vorhandener wird entfernt) |

## Was er anlegt
| | als root | rootless |
|---|---|---|
| Einstellungen | `/etc/trmm-web-relay/jumphost.env` | `~/.config/trmm-web-relay/jumphost.env` |
| Quellen des Images | `/etc/trmm-web-relay/src/` | `~/.config/trmm-web-relay/src/` |
| Quadlet | `/etc/containers/systemd/trmm-web-relay-jumphost.container` | `~/.config/containers/systemd/trmm-web-relay-jumphost.container` |
| Auto-Update | `/etc/systemd/system/trmm-web-relay-jumphost-update.{service,timer}` | `~/.config/systemd/user/trmm-web-relay-jumphost-update.{service,timer}` |
| Dienst | `trmm-web-relay-jumphost.service` | dito, als Benutzerdienst |
| Image | `localhost/trmm-web-relay-jumphost` | dito |
| Secret | `trmm-web-relay-api-key` | dito |
| Volume | `trmm-web-relay-jumphost` | dito |

Der Timer läuft sonntags um 4 Uhr mit bis zu 2 Stunden zufälliger Verzögerung und holt verpasste Läufe nach (`Persistent=true`).
