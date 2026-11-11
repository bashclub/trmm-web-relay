---
title: Updates
audience: Admin
outline: https://docs.bashclub.org/doc/updates-FcOU2s3dMG
outline_id: 76664b9d-1ac1-411b-b7f4-2e5af30e3318
---
## Client
### Neue Version erkennen
Ab 0.4 fragt der Client beim Start und danach einmal am Tag die neueste Version im Repository ab (`update_url`, [Konfiguration](../06-referenz/02-konfiguration.md)). Ist sie neuer als die installierte, steht auf der Steuerseite ein Hinweis mit den Befehlen zum Aktualisieren, und `trmm-web-relay check` meldet:
```
info  Version 0.5.0: neue Version 0.6.0 verfügbar (Handbuch: Updates)
```
Die installierte Version steht oben auf der Steuerseite neben dem Namen und in `trmm-web-relay --version`. Vor jedem Update den Abschnitt **Hinweise je Version** unten lesen.

### Mit lokaler Kopie
Wer wie im [Schnellstart](../01-schnellstart/_index.md) mit `git clone` installiert hat:
```bash
git -C trmm-web-relay pull
sh trmm-web-relay/install/client.sh
```
Unter Windows in PowerShell:
```powershell
git -C trmm-web-relay pull
powershell -ExecutionPolicy Bypass -File trmm-web-relay\install\client.ps1
```

### Ohne lokale Kopie
Wer mit `WR_SOURCE` direkt aus dem Repository installiert hat ([Client installieren](../03-installation/03-client.md#andere-quelle)), führt denselben Befehl noch einmal aus; der Installer holt dann den aktuellen Stand:
```bash
curl -fsSL https://code.bashclub.org/bashclub/trmm-web-relay/raw/branch/main/install/client.sh -o /tmp/wr-client.sh
WR_SOURCE=git+https://code.bashclub.org/bashclub/trmm-web-relay.git sh /tmp/wr-client.sh
```
Ohne Installer geht es auch direkt mit uv: `uv tool install --force git+https://code.bashclub.org/bashclub/trmm-web-relay.git`.

### Danach
Den laufenden Client mit **Beenden** oben auf der Steuerseite schließen und neu starten; ein laufender Client arbeitet sonst mit der alten Version weiter. Einstellungen, Schlüssel und Browserprofil bleiben.

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

## Hinweise je Version
Was eine Version über das Aktualisieren des Clients hinaus verlangt. Sprung-Host und Skripte in TRMM sind nur betroffen, wenn es hier steht.

### 0.5
- Neu: Symbol im Infobereich mit Menü zum Öffnen und Beenden, Befehl `trmm-web-relay stop` ([Die Steuerseite](../04-bedienung/01-steuerseite.md#symbol-im-infobereich)). Unter GNOME braucht das Symbol die Erweiterung AppIndicator ([Voraussetzungen](../03-installation/01-voraussetzungen.md#rechner-des-technikers)).
- Den Eintrag **Beenden** im Kontextmenü des Startsymbols (Linux) gibt es erst nach `trmm-web-relay desktop`; `install/client.sh` ruft das auf.
- Sprung-Host und Skripte in TRMM: nichts zu tun.

### 0.4
- Neu: Hinweis auf neue Versionen (siehe oben) und in der Einrichtung der Abschnitt **Browserprofil** für `direct_hosts` und die Zertifikatsprüfung.
- Sonst nichts zu tun.

### 0.3
- Das Browserprofil prüft Zertifikate. Geräte mit selbstsigniertem Zertifikat zeigen eine Warnung ([Verbinden und arbeiten](../04-bedienung/02-verbinden.md)). Das gilt erst, wenn alle Fenster des Profils einmal geschlossen waren: nach dem Update **Beenden**, alle Fenster des Profils schließen, neu starten.
- Erweiterungen und Passwortmanager im Profil möglich ([Erweiterungen und Passwortmanager](../04-bedienung/05-erweiterungen.md)).
- Sprung-Host und Skripte in TRMM: nichts zu tun.

## TRMM
Ein Update von TRMM ändert an Web-Relay nichts, solange die API gleich bleibt. Nach größeren Updates lohnt ein `trmm-web-relay check`.
