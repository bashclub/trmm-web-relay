---
title: TRMM-Skripte
audience: Admin
outline:
outline_id:
---
Die Einrichtung legt beide Skripte in TRMM an: Typ Shell, Plattformen Linux und macOS, Standard-Timeout 90 Sekunden, nicht als angemeldeter Benutzer. Die Quellen stehen in `trmm-scripts/` im Repository. Der Client vergleicht den Inhalt in TRMM mit seinem eigenen; jede Abweichung zeigt die Einrichtung als **veraltet oder von Hand geändert**.

## Web-Relay: Tunnel starten
Quelle `trmm-scripts/tunnel-start.sh`. Der Client startet es im Modus „nicht warten“ mit `max_hours` als Laufzeitgrenze.

| Argument | Beispiel | Bedeutung |
|---|---|---|
| 1 | `3f2a9c0d1e2f3a4b` | Sitzung, 16 Hexzeichen |
| 2 | `relay.example.com` | Sprung-Host |
| 3 | `22222` | Port des Sprung-Hosts |
| 4 | `wr-tunnel` | Konto |
| 5 | `20012` | Port auf dem Sprung-Host (Basis + Site-ID) |

| Umgebung | Inhalt |
|---|---|
| `WR_KEY` | Wegwerf-Schlüssel, base64 |
| `WR_CERT` | Zertifikat dazu, 15 Minuten gültig, base64 |
| `WR_KNOWN_HOSTS` | bestätigte Host-Schlüssel des Sprung-Hosts, base64 |

Ablauf: Argumente prüfen, Schlüssel nach `/tmp/wr-<sitzung>.XXXXXX/` schreiben (nur für root lesbar), `ssh -N -4 -R 127.0.0.1:<port>` zum Sprung-Host starten, den Schlüssel nach der Anmeldung löschen (spätestens nach 30 Sekunden), dann auf das Ende von `ssh` warten. `ssh` läuft als direktes Kind des Skripts, damit TRMM es bei Ablauf der Laufzeitgrenze mitbeendet. Es prüft den Host-Schlüssel streng und nutzt keine Konfiguration des Systems (`-F /dev/null`).

| Status | Bedeutung |
|---|---|
| 0 | Skript selbst beendet (Signal an das Skript) |
| 143 | `ssh` vom Stopp-Skript beendet, der Normalfall |
| 2 | ungültige Argumente oder Umgebung fehlt |
| 3 | `ssh` fehlt |
| 255 | `ssh` gescheitert: Sprung-Host nicht erreichbar, Host-Schlüssel falsch, Anmeldung abgelehnt |

## Web-Relay: Tunnel stoppen
Quelle `trmm-scripts/tunnel-stop.sh`, Timeout 60 Sekunden. Argument: die Sitzung. Beendet genau den `ssh`-Prozess dieser Sitzung (erkennbar am Schlüsselpfad) und räumt das Verzeichnis in `/tmp` auf. Status immer 0; die Ausgabe sagt, ob ein Tunnel aktiv war.

## Kennung
Beide Skripte tragen in der zweiten Kommentarzeile `trmm-web-relay-script <version>`. Daran erkennt man in TRMM, welche Fassung installiert ist.
