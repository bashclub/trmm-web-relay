---
title: Dateien und Pfade
audience: Admin
outline: https://docs.bashclub.org/doc/dateien-und-pfade-Zyn2PPCYUk
outline_id: ff78fac3-54a2-4969-a0e1-a53d50d34cde
---
## Client
Die Pfade gelten auf allen Systemen relativ zum Benutzerordner, unter Windows also z. B. `C:\Users\anna\.config\trmm-web-relay\`.

| Pfad | Inhalt |
|---|---|
| `~/.config/trmm-web-relay/config.toml` | Einstellungen, ohne Geheimnisse ([Konfiguration](02-konfiguration.md)) |
| `~/.local/share/trmm-web-relay/client.log` | Protokoll |
| `~/.local/share/trmm-web-relay/known_hosts` | bestätigte Host-Schlüssel der Sprung-Hosts |
| `~/.local/share/trmm-web-relay/browser/` | eigenes Browserprofil |
| `~/.local/share/trmm-web-relay/secrets/` | Geheimnisse, nur ohne nutzbaren Schlüsselbund (Rechte 0600) |
| `~/.cache/trmm-web-relay/erkannt.json` | erkannte Protokolle und Seitentitel der Ziele |
| `~/.cache/trmm-web-relay/version.json` | zuletzt abgefragte neueste Version (`update_url`) |
| `<Temp>/wr-<sitzung>-…/` | Wegwerf-Schlüssel und SSH-Log einer Sitzung, beim Beenden gelöscht |

## Schlüsselbund
Dienst `trmm-web-relay`, je Server:
| Name | Inhalt |
|---|---|
| `trmm-web-relay-<id>-api-key` | TRMM-API-Key |
| `trmm-web-relay-<id>-ca` | privater Schlüssel der CA |
| `trmm-web-relay-<id>-ca.pub` | öffentlicher Schlüssel der CA |

Linux: Secret Service (GNOME Schlüsselbund, KWallet), macOS: Schlüsselbund, Windows: Anmeldeinformationsverwaltung. Ohne nutzbaren Schlüsselbund liegen die Einträge als Dateien gleichen Namens im Ordner `secrets/`.

## Agent
| Pfad | Inhalt |
|---|---|
| `/tmp/wr-<sitzung>.XXXXXX/` | `known_hosts` und kurz der Schlüssel der Sitzung; das Start-Skript löscht den Ordner beim Ende |

## Sprung-Host
Siehe [Installer des Sprung-Hosts](05-installer-sprunghost.md#was-er-anlegt) und [Umgebung des Sprung-Hosts](04-umgebung-sprunghost.md#volume).

## Repository
| Pfad | Inhalt |
|---|---|
| `src/trmmwebrelay/` | Client |
| `trmm-scripts/` | Skripte für die Agenten |
| `jumphost/` | Image und `install.sh` des Sprung-Hosts |
| `install/` | Installer des Clients |
| `docs/handbuch/` | dieses Handbuch |
| `docs/adr/` | Entscheidungen |
