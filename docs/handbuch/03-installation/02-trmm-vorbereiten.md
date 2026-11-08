---
title: TRMM vorbereiten
audience: Admin
outline:
outline_id:
---
Web-Relay braucht zwei Arten von API-Keys: einen je Techniker für den Client und einen nur zum Lesen für den Sprung-Host. In TRMM gehört jeder API-Key zu einem Benutzer, und es zählen die Rechte von dessen Rolle. Ein Key, der einem anderen Benutzer gehört, bekommt 403, auch wenn die richtige Rolle existiert.

## Rolle für den Client
**Settings → Permissions Manager → Add Role**, Name z. B. `web-relay`. Keine Einschränkung auf Kunden oder Sites (sonst fehlen Sites in der Liste). Rechte:

| Recht | wofür |
|---|---|
| `List Clients` | Kunden und Sites mit ihren Feldern lesen |
| `List Agents` | Agenten einer Site, Online-Status, Plattform |
| `View Custom Fields` | die Felder **Tunnel-Ziele** und **Tunnel-Agent** finden |
| `List Scripts` | die Tunnel-Skripte finden und mit dem Stand im Client vergleichen |
| `Run Scripts` | Tunnel starten und stoppen |
| `Manage Sites` | Ziele und Tunnel-Agenten in der Steuerseite bearbeiten (optional) |
| `Manage Custom Fields` | Felder aus der Einrichtung anlegen (nur einmal je TRMM) |
| `Manage Scripts` | Skripte aus der Einrichtung anlegen und aktualisieren |

`Manage Custom Fields` und `Manage Scripts` braucht nur, wer die Einrichtung für den TRMM-Server zum ersten Mal macht oder nach einem Update die Skripte aktualisiert. Danach kann man sie wieder entziehen. `Manage Sites` ist das schmalste Recht, mit dem TRMM das Schreiben von Site-Feldern erlaubt; es erlaubt auch, Sites umzubenennen. Wer Ziele lieber in TRMM selbst pflegt, lässt es weg. `List Sites` ist nicht nötig, die Sites kommen über `/clients/`.

## Benutzer und Key je Techniker
1. **Settings → User Administration → Add User**: Benutzer z. B. `web-relay-anna`, Rolle `web-relay`. **Deny Dashboard Logins** darf gesetzt sein, der Benutzer braucht nur die API.
2. **Settings → Global Settings → API Keys → Add Key**: Name z. B. `web-relay anna-laptop`, **Benutzer** `web-relay-anna`, Ablauf nach Wunsch.
3. Den Key kopieren. Er wird in der Einrichtung des Clients eingetragen und landet dort im Schlüsselbund.

Je Techniker ein eigener Benutzer: Dann zeigt das Audit-Log, wer welchen Tunnel gestartet hat, und einen Techniker sperrt man, indem man seinen Key löscht.

## Rolle und Key für den Sprung-Host
Der Sprung-Host liest alle 5 Minuten Sites und öffentliche Adressen der Agenten. Rolle z. B. `web-relay-jumphost`, ohne Einschränkung auf Kunden, nur mit `List Clients` und `List Agents`. Dazu ein Benutzer mit **Deny Dashboard Logins** und ein Key für ihn. Den Key fragt der Installer des Sprung-Hosts ab.

## Felder und Skripte
Die beiden Benutzerfelder an Sites und die beiden Skripte legt die [Einrichtung im Client](04-einrichtung.md) an. Wer sie von Hand anlegen will: Felder unter **Settings → Global Settings → Custom Fields**, Ziel **Site**, Typ **Text**, Namen **Tunnel-Ziele** und **Tunnel-Agent**. Die Skripte stehen in `trmm-scripts/` im Repository; die Einrichtung meldet sie als veraltet, wenn ihr Inhalt abweicht. Andere Namen für Felder und Skripte lassen sich in der [Konfiguration](../06-referenz/02-konfiguration.md) einstellen.
