---
title: Client installieren
audience: Admin
outline:
outline_id:
---
Der Client ist ein Python-Programm. Der Installer richtet es mit [uv](https://docs.astral.sh/uv/) als eigenständiges Werkzeug ein; uv bringt ein passendes Python mit, eine Python-Installation im System ist nicht nötig. Der Installer legt danach das Startsymbol an.

## Linux und macOS
```bash
git clone https://code.bashclub.org/bashclub/trmm-web-relay.git
sh trmm-web-relay/install/client.sh
```
Der Installer:
1. prüft, ob `ssh` vorhanden ist,
2. installiert `uv` nach `~/.local/bin`, falls es fehlt,
3. installiert den Client (`uv tool install`) als Befehl `trmm-web-relay` in `~/.local/bin`,
4. legt das Symbol **TRMM Web-Relay** auf dem Desktop und im Anwendungsmenü an (Linux: `.desktop`-Datei, macOS: `~/Applications/TRMM Web-Relay.app` mit Verknüpfung auf dem Schreibtisch).

## Windows
In PowerShell:
```powershell
git clone https://code.bashclub.org/bashclub/trmm-web-relay.git
powershell -ExecutionPolicy Bypass -File trmm-web-relay\install\client.ps1
```
Fehlt der OpenSSH-Client: **Einstellungen → System → Optionale Features → OpenSSH-Client** hinzufügen. Das Symbol landet auf dem Desktop und im Startmenü und startet den Client ohne Konsolenfenster.

## Aktualisieren
```bash
git -C trmm-web-relay pull
sh trmm-web-relay/install/client.sh
```
Danach den laufenden Client mit **Beenden** oben auf der Steuerseite schließen und neu starten. Einstellungen und Schlüssel bleiben. Was nach einem Update zu tun ist, steht in [Updates](../05-betrieb/01-updates.md).

## Andere Quelle
Ohne lokale Kopie direkt aus dem Repository, z. B. für eine Verteilung per Softwareverteilung:
```bash
curl -fsSL https://code.bashclub.org/bashclub/trmm-web-relay/raw/branch/main/install/client.sh -o /tmp/wr-client.sh
WR_SOURCE=git+https://code.bashclub.org/bashclub/trmm-web-relay.git sh /tmp/wr-client.sh
```
`WR_SOURCE` nimmt alles, was `uv tool install` versteht, auch einen Tag (`git+https://…@v0.2.0`) oder einen eigenen Fork.

## Ohne Installation
Zum Ausprobieren oder Entwickeln direkt aus dem Repository (Python ab 3.11):
```bash
cd trmm-web-relay
PYTHONPATH=src python3 -m trmmwebrelay
```
Ohne das Paket `keyring` liegen die Geheimnisse dann als Dateien in `~/.local/share/trmm-web-relay/secrets/` (Rechte 0600).

## Entfernen
```bash
trmm-web-relay desktop --remove
uv tool uninstall trmm-web-relay
```
Einstellungen (`~/.config/trmm-web-relay`), Browserprofil und Log (`~/.local/share/trmm-web-relay`) bleiben; API-Keys und CA löscht man vorher in der Einrichtung mit **Entfernen** beim Server.
