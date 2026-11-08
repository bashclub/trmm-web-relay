---
title: Updates
audience: Admin
outline: https://docs.bashclub.org/doc/updates-FcOU2s3dMG
outline_id: 76664b9d-1ac1-411b-b7f4-2e5af30e3318
---
## Client
```bash
git -C trmm-web-relay pull
sh trmm-web-relay/install/client.sh
```
Danach den Client mit **Beenden** schließen und neu starten. Unter Windows `install\client.ps1` statt `client.sh`.

## Skripte in TRMM
Bringt ein Update neue Fassungen der Tunnel-Skripte mit, zeigt die Einrichtung bei **Prüfen** die Skripte als **veraltet oder von Hand geändert**. **In TRMM aktualisieren** schreibt die neue Fassung; der Key braucht dafür `Manage Scripts`. Das macht einer je TRMM-Server. Bis dahin laufen Tunnel mit der alten Fassung weiter, sofern das Update nichts anderes sagt.

## Sprung-Host
### Auto-Update
Der Installer richtet den Timer `trmm-web-relay-jumphost-update.timer` ein: sonntags zwischen 4 und 6 Uhr, verpasste Läufe holt er nach. Er baut das Image ohne Cache mit frischer Debian-Basis und aktuellen Paketen neu und vergleicht die installierten Pakete mit dem laufenden Image. Nur wenn sich etwas geändert hat, startet er den Dienst neu; offene Tunnel brechen dann ab und lassen sich sofort neu verbinden.

Nächsten Lauf und letztes Ergebnis ansehen:
```bash
systemctl list-timers trmm-web-relay-jumphost-update.timer
journalctl -u trmm-web-relay-jumphost-update.service -n 20
```
Von Hand auslösen:
```bash
systemctl start trmm-web-relay-jumphost-update.service
```
Rootless jeweils mit `systemctl --user` und `journalctl --user`.

Abschalten: den Installer mit `AUTO_UPDATE=0` erneut ausführen.
```bash
AUTO_UPDATE=0 bash trmm-web-relay-sprunghost-*.sh
```

### Neue Fassung des Sprung-Hosts
Das Auto-Update aktualisiert nur Pakete. Änderungen am Sprung-Host selbst (`sshd_config`, Skripte im Image) kommen mit einem neuen Installer: Client aktualisieren, in der Einrichtung **Installer herunterladen** und auf dem Server ausführen. Einstellungen, Secret und Host-Schlüssel bleiben.

Bei [eigenem Deployment](../03-installation/07-eigenes-deployment.md) das Image aus dem aktualisierten Ordner `jumphost/` neu bauen.

## TRMM
Ein Update von TRMM ändert an Web-Relay nichts, solange die API gleich bleibt. Nach größeren Updates lohnt ein `trmm-web-relay check`.
