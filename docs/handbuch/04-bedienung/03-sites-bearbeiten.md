---
title: Sites bearbeiten
audience: Anwender
outline:
outline_id:
---
Websites und Tunnel-Agenten einer Site stehen in TRMM in zwei Benutzerfeldern an der Site. Die Steuerseite bearbeitet sie direkt; der API-Key braucht dafür das Recht `Manage Sites`. Ohne das Recht pflegt man die Felder in TRMM selbst (Site bearbeiten → Custom Fields), im [Format der Felder](../06-referenz/03-site-felder.md).

## Editor öffnen
Haken bei **auch Sites ohne Ziele**, wenn die Site noch keine Ziele hat. Dann **Bearbeiten** bei der Site. Während der Editor offen ist, baut die Seite die Liste nicht neu auf.

## Websites
Je Zeile ein Ziel:
- **Name (optional)**: so heißt der Link, z. B. `Firewall`. Leer: der Seitentitel des Geräts.
- **Adresse**: `host:port`, `host` oder eine URL, z. B. `192.168.1.1:8443`, `192.168.1.10`, `https://nas.local:5001/`, `http://192.168.1.20/admin/`.

Ohne Protokoll probiert der Client HTTPS und HTTP und nimmt, was antwortet. Ohne Port probiert er 443 und 80. Die Reihenfolge mit ↑ und ↓ ist die Reihenfolge der Links, ✕ entfernt eine Zeile, **+ Website** fügt eine hinzu. Nicht erlaubt sind `|`, `;` und Leerzeichen in der Adresse und `|` oder `;` im Namen.

## Tunnel-Agenten
Die Liste legt fest, welcher Agent den Tunnel baut. Der Client nimmt den ersten, der online ist und Linux oder macOS hat. **Agent hinzufügen …** zeigt alle Agenten der Site mit Plattform und Status; Agenten unter Windows sind ausgegraut. ↑ und ↓ ändern die Priorität.

Bleibt die Liste leer oder ist keiner davon online, nimmt der Client einen anderen passenden Agenten der Site, Server vor Workstations. Eintragen lohnt sich, wenn ein bestimmtes Gerät die Ziele erreicht (z. B. im Management-VLAN) oder wenn man Workstations nicht nutzen will.

## Speichern
**In TRMM speichern** schreibt beide Felder der Site in TRMM und lädt die Liste neu. **Abbrechen** verwirft die Änderungen. Fehlt das Recht `Manage Sites`, meldet der Editor das; der Entwurf bleibt dann stehen.

Die Änderung steht im Audit-Log von TRMM unter dem Benutzer des API-Keys. Andere Techniker sehen sie nach **Neu laden**.
