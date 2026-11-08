---
title: Logs
audience: Admin
outline: https://docs.bashclub.org/doc/logs-YxOCHCCnM1
outline_id: 55012d6e-11d9-47c4-8a0f-3c50cbcd6c6c
---
## Client
`~/.local/share/trmm-web-relay/client.log` (unter Windows `%USERPROFILE%\.local\share\trmm-web-relay\client.log`), rotiert bei 1 MB, zwei alte Dateien. Mit `trmm-web-relay -v` schreibt der Client ausführlicher. Geheimnisse stehen nie im Log.

## TRMM
- **Verlauf des Agenten** (Agent → History): je Tunnel ein Lauf von **Web-Relay: Tunnel starten** mit den Argumenten `<sitzung> <sprunghost> <port> wr-tunnel <fernport>` und am Ende ein Lauf von **Web-Relay: Tunnel stoppen** mit derselben Sitzung. Die Ausgabe des Start-Skripts endet mit `Tunnel <sitzung> beendet (ssh-Status …)`.
- **Audit-Log** (Settings → Audit Log): wer welches Skript wann ausgeführt hat und wer Site-Felder geändert hat.

## Sprung-Host
Alles geht ins Journal:
```bash
journalctl -t sshd --since today
podman logs --since 1h trmm-web-relay-jumphost
```

Beim Start:
```
Host-Schlüssel: 256 SHA256:… jumphost (ED25519)
Vertraute CA: 256 SHA256:… trmm-web-relay-ca msp anna@laptop (ED25519)
Clients nur aus: 203.0.113.7/32 10.8.0.0/24
Sites in TRMM: 42
```
Beim Abgleich mit TRMM (alle 5 Minuten, nur Änderungen):
```
Site 12: erlaubte Absender 198.51.100.23
Site 7: kein Agent online, keine Absender aus TRMM
TRMM-Abgleich fehlgeschlagen, letzte Liste bleibt
```
Bei einer Anmeldung des Agenten, mit der Kennung aus dem Zertifikat:
```
Accepted publickey for wr-tunnel from 198.51.100.23 port 51234 ssh2: ED25519-CERT SHA256:… ID site-12 pve01 sitzung=3f2a9c… von=anna@laptop (serial …) CA ED25519 SHA256:…
```
Abgelehnte Anmeldungen:
| Zeile | Bedeutung |
|---|---|
| `Authentication tried for wr-tunnel with valid certificate but not from a permitted host` | Absender ist keine bekannte Adresse eines Agenten der Site |
| Zeile mit `Certificate invalid` und `expired` bzw. `not yet valid` | Zertifikat abgelaufen oder noch nicht gültig: Uhr von Client oder Sprung-Host falsch, oder der Agent hat den Auftrag erst nach mehr als 15 Minuten abgeholt |
| `Failed publickey for wr-tunnel …` bzw. `wr-admin` | Zertifikat nicht von einer CA aus `TRUSTED_CA` oder falscher Principal |
| `User wr-admin from … not allowed because not listed in AllowUsers` | Client außerhalb von `ADMIN_FROM` |

## Eine Sitzung nachvollziehen
Die Sitzungskennung (16 Hexzeichen) steht in allen drei Logs: im Client-Log, in den Argumenten der Skriptläufe in TRMM und in der Kennung des Zertifikats auf dem Sprung-Host. Damit findet man zu einer Anmeldung auf dem Sprung-Host den Techniker (`von=`), den Agenten und den TRMM-Benutzer.
```bash
sitzung=3f2a9c0d1e2f3a4b
journalctl -t sshd | grep "sitzung=$sitzung"
```
