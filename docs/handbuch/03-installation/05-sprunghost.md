---
title: Sprung-Host installieren
audience: Admin
outline: https://docs.bashclub.org/doc/sprung-host-installieren-wrP4hZCGSX
outline_id: 75e1a6c3-31a4-4d54-be4e-8897430ff531
---
Den Installer für den Sprung-Host erzeugt der Client in der Einrichtung. Er ist eine einzelne Datei `trmm-web-relay-sprunghost-<server>.sh` mit den Quellen des Images, `install.sh` und den öffentlichen Werten dieses Servers (TRMM-Adresse, CA, Port). Geheimnisse enthält er nicht; den TRMM-Key fragt er auf dem Server ab.

## Installieren
Datei auf den Server kopieren und als root ausführen:
```bash
bash trmm-web-relay-sprunghost-*.sh
```
Der Installer fragt nach:
- dem **TRMM-API-Key nur zum Lesen** (Rechte `List Clients`, `List Agents`, siehe [TRMM vorbereiten](02-trmm-vorbereiten.md)). Er landet als Podman-Secret `trmm-web-relay-api-key`, nicht in einer Datei.
- den **IPv4-Netzen der Techniker** (`ADMIN_FROM`), mit Leerzeichen getrennt, z. B. `203.0.113.7/32 10.8.0.0/24`. Nur aus diesen Netzen dürfen sich Clients anmelden. Leer heißt: von überall.

Dann baut er das Image `localhost/trmm-web-relay-jumphost`, schreibt Einstellungen und Quadlet, startet den Dienst `trmm-web-relay-jumphost.service` und richtet den Timer für das [Auto-Update](../05-betrieb/01-updates.md#sprung-host) ein. Am Ende zeigt er die letzten Zeilen des Logs und den **Fingerabdruck** des Host-Schlüssels:
```
==> Fertig. Der Sprung-Host lauscht auf TCP 22222 (nur IPv4).
==> Fingerabdruck zum Vergleich im Client: 256 SHA256:… jumphost (ED25519)
==> Firewall/Portweiterleitung: TCP 22222 von außen auf diesen Server freigeben.
```

## Firewall
TCP **22222** (bzw. `PUBLIC_PORT`) aus dem Internet auf den Server freigeben oder weiterleiten, nur IPv4. Agenten kommen von beliebigen Adressen ihrer Kunden; die Prüfung, wer welche Site öffnen darf, macht der Sprung-Host selbst. Einen DNS-Namen (z. B. `relay.example.com`) nur als A-Eintrag anlegen, ohne AAAA.

Läuft eine Sperrliste wie CrowdSec vor dem Sprung-Host, gehören die Adressen der Agenten in deren Allowlist: [CrowdSec](../05-betrieb/03-crowdsec.md).

## Ohne root
Der Installer läuft auch als eigener Dienstbenutzer (rootless Podman). Dann landen Quadlet, Einstellungen und Timer unter `~/.config`, und der Dienst läuft als Benutzerdienst. Damit er nach dem Abmelden und beim Booten läuft, braucht der Benutzer Linger. Als root, hier für den Benutzer `trmm-relay`:
```bash
user=trmm-relay
loginctl enable-linger "$user"
```

Ports unter 1024 gehen rootless nur mit angepasstem `net.ipv4.ip_unprivileged_port_start`; 22222 ist davon nicht betroffen. Rootless Podman mit pasta reicht die echte Absenderadresse durch, die Absenderprüfung funktioniert also.

## Werte vorgeben
Alle Abfragen lassen sich per Umgebung vorgeben, z. B. für eine Installation ohne Rückfragen:
```bash
read -rs TRMM_API_KEY && export TRMM_API_KEY
ADMIN_FROM="203.0.113.7/32 10.8.0.0/24" PUBLIC_PORT=22222 bash trmm-web-relay-sprunghost-*.sh
```
Alle Variablen und Optionen: [Installer des Sprung-Hosts](../06-referenz/05-installer-sprunghost.md).

## Erneut ausführen
Ein zweiter Lauf aktualisiert: Er baut das Image neu, behält `ADMIN_FROM`, `ALLOW_FROM`, Port und Secret und fügt eine neue CA zu den vorhandenen hinzu. So kommen [weitere Techniker](06-weitere-techniker.md) dazu und neue Fassungen des Sprung-Hosts auf den Server.

## Prüfen
```bash
systemctl status trmm-web-relay-jumphost.service
podman logs trmm-web-relay-jumphost
```
Im Log stehen nach dem Start der Host-Schlüssel, je CA eine Zeile `Vertraute CA: …`, `Clients nur aus: …` und nach dem ersten Abgleich `Sites in TRMM: <Anzahl>`. Fehlt die letzte Zeile, scheitert die Abfrage von TRMM, siehe [Typische Fehler](../07-fehlerbehebung/02-typische-fehler.md).

## Entfernen
```bash
bash trmm-web-relay-sprunghost-*.sh --uninstall
```
Entfernt Dienst, Timer, Image und Secret. Einstellungen (`/etc/trmm-web-relay/jumphost.env`) und das Volume `trmm-web-relay-jumphost` mit dem Host-Schlüssel bleiben, damit eine neue Installation denselben Fingerabdruck hat.
