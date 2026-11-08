---
title: Sicherheitsmodell
audience: Admin
outline: https://docs.bashclub.org/doc/sicherheitsmodell-lkQevkkYfl
outline_id: e992e6fd-a110-4b56-8bf0-14756db1e53c
---
Web-Relay soll keinen neuen dauerhaften Zugang schaffen. Es nutzt das Vertrauen, das TRMM schon hat: Wer TRMM steuert, kann auf den Agenten ohnehin Skripte als root ausführen. Dazu kommen drei Grenzen: kurzlebige Zertifikate, eine Absenderprüfung auf dem Sprung-Host und ein Browserprofil, das außer den Zielen aktiver Sitzungen nur wenige freigegebene Hosts erreicht.

## Wer wem vertraut
| Teil | vertraut | Schlüssel |
|---|---|---|
| Sprung-Host | den CAs der Clients in `TRUSTED_CA` | keine einzelnen Benutzerschlüssel |
| Client | seinem Schlüsselbund (API-Key, CA) und dem bestätigten Host-Schlüssel des Sprung-Hosts | eigene `known_hosts`, nicht `~/.ssh/known_hosts` |
| Agent | TRMM (Skript und Umgebung kommen von dort) und dem Host-Schlüssel, den der Client mitgibt | Wegwerf-Schlüssel je Sitzung |

## Zertifikate statt Schlüssel
Jeder Client hat je TRMM-Server eine eigene SSH-CA im Schlüsselbund des Systems. Für jede Sitzung erzeugt er zwei Wegwerf-Schlüssel und signiert sie für 15 Minuten. Ein Zertifikat gilt nur für die Anmeldung; der Tunnel läuft danach weiter, bis eine Seite ihn beendet. Ein abgegriffener Schlüssel ist nach 15 Minuten wertlos.

Auf dem Sprung-Host gibt es nur drei Konten, alle ohne Shell und Passwort:
| Konto | wer | Principal | darf |
|---|---|---|---|
| `wr-tunnel` | Tunnel-Skript auf dem Agenten | `site-<ID>` | nur `127.0.0.1:<20000+ID>` öffnen (`-R`), nur von erlaubten Absendern |
| `wr-admin` | Client des Technikers | `wr-admin` | nur zu `127.0.0.1:*` weiterleiten (`-L`), auf Wunsch nur aus `ADMIN_FROM` |
| `wr-keys` | intern für `sshd` | – | keine Anmeldung |

Ein Zertifikat für Site 1 öffnet also nie den Port von Site 2, und ein Client-Zertifikat kann keinen Tunnel anbieten. Neue Sites brauchen am Sprung-Host nichts.

## Absenderprüfung
Der Sprung-Host fragt TRMM alle 5 Minuten nach allen Sites und den öffentlichen IPv4-Adressen der Agenten, die online sind. Ein Zertifikat für `site-<ID>` nimmt er nur an, wenn die Verbindung von der öffentlichen IPv4 eines Agenten dieser Site kommt oder aus einem festen Netz in `ALLOW_FROM`. Wer Schlüssel und Zertifikat eines Agenten abgreift, kann damit von woanders nichts anfangen. Darum ist der Sprung-Host nur über IPv4 erreichbar: TRMM liefert die öffentliche Adresse der Agenten nur als IPv4.

## Browserprofil und Verteiler
Der Client startet den Browser mit einem eigenen Profil, das alle Verbindungen an den lokalen SOCKS-Verteiler schickt. Der lässt Ziele und Netze aktiver Sitzungen durch den Tunnel, dazu direkt ins Internet nur den Web Store für Erweiterungen und die Hosts in `direct_hosts` (etwa den Server eines Passwortmanagers). Alles andere lehnt er ab. So kann keine beliebige Webseite in diesem Profil laufen und im Hintergrund Anfragen an Geräte im Kundennetz schicken. Zertifikate prüft das Profil wie ein normaler Browser; selbstsignierte Zertifikate der Geräte zeigen eine Warnung, durch die man sich klickt. Die Ausnahme `ignore_cert_errors` gilt für alle Verbindungen des Profils, auch die zum Passwortmanager. Die Steuerseite nimmt nur Anfragen an `127.0.0.1` bzw. `localhost` an; Aktionen brauchen einen eigenen Header, den fremde Webseiten nicht setzen können.

## Was ein Angreifer bräuchte
- **Den API-Key eines Technikers**: Damit kann er in TRMM Skripte starten, so weit die Rolle reicht. Das ist dasselbe Risiko wie ohne Web-Relay. Tunnel bauen kann er damit allein nicht, dafür fehlt ihm die CA.
- **Die CA eines Clients**: Damit kann er Zertifikate für alle Sites dieses TRMM-Servers ausstellen. Er braucht aber zusätzlich einen Agenten, der den Tunnel baut (also TRMM-Zugriff), oder er muss aus `ADMIN_FROM` kommen, um sich an bestehende Tunnel zu hängen. Deshalb gehört `ADMIN_FROM` auf die Netze der Techniker gesetzt.
- **Zugriff auf den Sprung-Host**: Wer root auf dem Server hat, kann an den Tunnel-Ports mithören. Der Sprung-Host gehört behandelt wie TRMM selbst: aktuell, gehärtet, nur der eine Port offen.

Schlüssel und Zertifikat für den Agenten gehen als Umgebungsvariablen über TRMM. Wer in TRMM die Skriptläufe einsehen kann, kann sie unter Umständen lesen. Sie gelten nur 15 Minuten, nur für den Port dieser Site und nur von deren Absenderadressen.

## Nachvollziehbarkeit
- **TRMM**: Jeder Tunnel ist ein Skriptlauf mit Benutzer, Agent und Zeit im Verlauf und im Audit-Log.
- **Sprung-Host**: Jede Anmeldung steht im Log (`LogLevel VERBOSE`) mit der Kennung des Zertifikats, z. B. `site-12 fw-host sitzung=3f2a… von=anna@laptop`, und jede abgelehnte Anmeldung mit Grund. Siehe [Logs](../05-betrieb/02-logs.md).
- **Client**: `~/.local/share/trmm-web-relay/client.log`.

## Empfehlungen
- Je Techniker ein eigener TRMM-Benutzer mit eigenem Key; nie einen Key teilen.
- Schreibrechte (`Manage …`) nur geben, solange sie gebraucht werden.
- `ADMIN_FROM` auf VPN oder Büro des MSP setzen.
- TRMM härten: 2FA, Weboberfläche nur aus bekannten Netzen, Updates. TRMM ist der Schlüssel zu allem.
- Ausscheidende Techniker: [Zugang entziehen](../05-betrieb/04-zugang-entziehen.md).
