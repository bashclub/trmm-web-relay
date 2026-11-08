---
title: Einrichtung im Client
audience: Admin
outline: https://docs.bashclub.org/doc/einrichtung-im-client-TSFfWFvbrl
outline_id: 7b6f7f94-4aa0-4a46-adf6-3e4ff0d01c43
---
Die Einrichtung ist eine Seite des Clients (`http://127.0.0.1:8765/einrichtung`). Beim ersten Start öffnet sie sich von selbst, später über **Einrichtung** oben auf der Steuerseite. Sie prüft je Server Schritt für Schritt, was fehlt, und erledigt es auf Knopfdruck. Was in TRMM schreibt, fragt vorher nach.

## Server anlegen
**Server hinzufügen**:
| Feld | Inhalt |
|---|---|
| Name | frei, z. B. der Name des MSP oder der TRMM-Instanz |
| TRMM-API-Adresse | z. B. `https://api.example.com`, die Adresse der API, nicht der Weboberfläche |
| API-Key | der Key des Technikers ([TRMM vorbereiten](02-trmm-vorbereiten.md)); wird im Schlüsselbund gespeichert, beim Bearbeiten leer lassen = unverändert |
| Sprung-Host | `host:port`, unter dem Agenten **und** dieser Rechner den Sprung-Host erreichen, z. B. `relay.example.com:22222`; kann auch später folgen |

**Speichern und prüfen** speichert und startet die Prüfung.

## Die Prüfung
Die Punkte erscheinen in dieser Reihenfolge:

| Punkt | ok, wenn | sonst |
|---|---|---|
| TRMM `https://…` | Key gültig, Lesen erlaubt | fehlende Rechte werden genannt |
| Schreibrechte des API-Keys | `Manage Sites`, `Manage Scripts`, `Manage Custom Fields` vorhanden | Hinweis (kein Fehler), welche Knöpfe ohne sie nicht gehen |
| Feld „Tunnel-Ziele“ an Sites | Feld existiert | **In TRMM anlegen** |
| Feld „Tunnel-Agent“ an Sites | Feld existiert | **In TRMM anlegen** |
| Skript „Web-Relay: Tunnel starten“ | Inhalt gleich dem des Clients | **In TRMM anlegen** bzw. **In TRMM aktualisieren** |
| Skript „Web-Relay: Tunnel stoppen“ | wie oben | wie oben |
| Sprung-Host `host:port` | Host-Schlüssel bestätigt | **Fingerabdruck bestätigen** |
| CA dieses Clients | CA im Schlüsselbund | **CA erzeugen** |
| Anmeldung am Sprung-Host | Testanmeldung mit Zertifikat klappt | Fehlermeldung von `ssh` mit Hinweis |

Die Schreibrechte prüft der Client, ohne etwas zu ändern: Er schickt eine Änderung an eine Kennung, die es nicht gibt. Antwortet TRMM mit 404, ist das Recht da, bei 403 fehlt es.

## Reihenfolge beim ersten Mal
1. Felder und Skripte in TRMM anlegen.
2. **CA erzeugen**. Die Zeile, die danach unter **CA dieses Clients** steht, ist der öffentliche Schlüssel; er ist kein Geheimnis.
3. Unter **Sprung-Host installieren oder aktualisieren** den **Installer herunterladen** und den [Sprung-Host installieren](05-sprunghost.md).
4. **Neu prüfen**, den Fingerabdruck des Sprung-Hosts mit der Ausgabe des Installers vergleichen und **Fingerabdruck bestätigen**.
5. **Anmeldung am Sprung-Host: ok**. Fertig, **Zu den Sites**.

## Host-Schlüssel des Sprung-Hosts
Der Client führt eine eigene `known_hosts` (`~/.local/share/trmm-web-relay/known_hosts`), getrennt von `~/.ssh/known_hosts`. Er gibt die bestätigten Schlüssel bei jedem Tunnel an den Agenten mit, damit auch der nur mit dem echten Sprung-Host spricht. Ändert sich der Host-Schlüssel, meldet die Prüfung das als Fehler. Nur bestätigen, wenn der Sprung-Host wirklich neu aufgesetzt wurde.

## Server bearbeiten und entfernen
Jeder Server hat in der Liste oben die Knöpfe **Prüfen**, **Bearbeiten** und **Entfernen**.
**Bearbeiten** ändert Name, Adressen und Key. **Entfernen** löscht den Server aus der Konfiguration und API-Key und CA dieses Clients aus dem Schlüsselbund. Danach akzeptiert der Sprung-Host eine neue CA dieses Clients erst, wenn sie in `TRUSTED_CA` steht.

Auf der Kommandozeile prüft `trmm-web-relay check` dasselbe für alle Server, nur lesend.
