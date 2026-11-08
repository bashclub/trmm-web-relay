---
title: TRMM-Rechte
audience: Admin
outline:
outline_id:
---
In TRMM gehört jeder API-Key einem Benutzer; es zählen die Rechte von dessen Rolle (Settings → Permissions Manager). Änderungen an der Rolle wirken sofort. Die Rolle darf nicht auf Kunden oder Sites eingeschränkt sein, sonst fehlen Sites oder Agenten.

## Client (Key je Techniker)
| Recht | Endpunkt | wofür | nötig |
|---|---|---|---|
| `List Clients` | `GET /clients/` | Kunden, Sites, Feldwerte | immer |
| `List Agents` | `GET /agents/` | Agenten, Status, Plattform, Netze | immer |
| `View Custom Fields` | `GET /core/customfields/` | Felder finden | immer |
| `List Scripts` | `GET /scripts/` | Skripte finden und vergleichen | immer |
| `Run Scripts` | `POST /agents/<id>/runscript/` | Tunnel starten und stoppen | immer |
| `Manage Sites` | `PUT /clients/sites/<id>/` | Ziele und Tunnel-Agenten in der Steuerseite speichern | optional |
| `Manage Custom Fields` | `POST /core/customfields/` | Felder aus der Einrichtung anlegen | einmal je TRMM |
| `Manage Scripts` | `POST`/`PUT /scripts/` | Skripte anlegen und aktualisieren | einmal und nach Updates |

Die Einrichtung prüft die Leserechte mit echten Abfragen. Die Schreibrechte prüft sie, ohne etwas zu ändern: mit einer Änderung an einer Kennung, die es nicht gibt (403: Recht fehlt, 404: Recht vorhanden). `Run Scripts` zeigt sich erst beim ersten Verbinden.

## Sprung-Host (ein Key nur zum Lesen)
| Recht | Endpunkt | wofür |
|---|---|---|
| `List Clients` | `GET /clients/` | alle Site-IDs |
| `List Agents` | `GET /agents/` | öffentliche IPv4 und Status der Agenten je Site |

Keine weiteren Rechte. Benutzer mit **Deny Dashboard Logins**.

## Typische Fehler
- **403 trotz richtiger Rolle**: Der Key gehört einem anderen Benutzer. In der Liste der API-Keys steht, zu welchem Benutzer er gehört.
- **Sites fehlen**: Die Rolle ist auf Kunden eingeschränkt, oder dem Benutzer sind nur bestimmte Kunden zugewiesen.
