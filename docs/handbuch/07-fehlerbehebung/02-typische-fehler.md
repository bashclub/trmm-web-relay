---
title: Typische Fehler
audience: Admin
outline: https://docs.bashclub.org/doc/typische-fehler-ZWQl3R5CiH
outline_id: 112d4af6-ad09-4d51-b816-5a64b7ba8661
---
## Permission denied beim Agenten
Meldung: **Tunnel vom Agenten kam nicht innerhalb von 90 s an**, im Verlauf des Agenten `Permission denied (publickey)`, im Log des Sprung-Hosts `not from a permitted host`.

Der Sprung-Host nimmt die Anmeldung nur von der öffentlichen IPv4 eines Agenten der Site an, wie TRMM sie kennt. Ursachen:
- **Adresse frisch geändert** (dynamische IP, neuer Anschluss): Der Sprung-Host gleicht alle 5 Minuten ab. Warten und erneut verbinden.
- **Agent ging über IPv6 zu TRMM**: TRMM kennt dann keine öffentliche IPv4 des Agenten. In TRMM bei den Agenten der Site die Spalte **Public IP** prüfen.
- **Anderer Weg ins Internet**: Agent erreicht TRMM über einen anderen Anschluss als den Sprung-Host (Proxy, zweite Leitung, VPN). Dann die Adresse, von der er kommt, in `ALLOW_FROM` eintragen.
- **Abgleich scheitert**: Im Log steht `TRMM-Abgleich fehlgeschlagen`. Siehe unten.

## Sites in TRMM fehlt im Log
Der Sprung-Host erreicht die TRMM-API nicht oder der Key passt nicht. Im Log steht `TRMM-Abgleich fehlgeschlagen, letzte Liste bleibt` oder `Key fehlt`. Prüfen:
```bash
podman exec trmm-web-relay-jumphost sh -c 'curl -sS -o /dev/null -w "%{http_code}\n" -H "X-API-KEY: $(cat /run/secrets/trmm-api-key)" "$(cat /run/jumphost/trmm_url)/clients/"'
```
`200` ist richtig. `403`: Key ohne `List Clients` oder Allowlist vor der API (siehe Hairpin in [Eigenes Deployment](../03-installation/07-eigenes-deployment.md)). `401`: Key falsch, mit dem Installer und `TRMM_API_KEY` neu setzen.

## Anmeldung am Sprung-Host: Permission denied
Punkt **Anmeldung am Sprung-Host** in der Einrichtung. Ursachen:
- Die CA dieses Clients steht nicht in `TRUSTED_CA`: Installer aus dieser Einrichtung auf dem Sprung-Host ausführen.
- Dieser Rechner ist nicht in `ADMIN_FROM`: im Log `not listed in AllowUsers`. Netz ergänzen oder aus dem VPN des MSP arbeiten.

## Host-Schlüssel hat sich geändert
Der Sprung-Host meldet sich mit einem anderen Schlüssel als bestätigt. Wurde er neu aufgesetzt (ohne gesichertes Volume), den neuen Fingerabdruck mit `podman logs trmm-web-relay-jumphost` vergleichen und bestätigen. Wenn nicht: nicht bestätigen, Netzweg und DNS prüfen.

## Kein Agent für den Tunnel verfügbar
In der Site ist kein Agent unter Linux oder macOS online. Der Hinweis nennt die übersprungenen Agenten mit Grund (`offline`, `windows wird noch nicht unterstützt`, `kein TRMM-Agent`). Einen passenden Agenten in die Site bringen oder den Hostnamen im Feld **Tunnel-Agent** korrigieren.

## Skript „…“ fehlt in TRMM
Die Skripte fehlen in TRMM oder heißen anders. In der Einrichtung **Prüfen** und anlegen; bei eigenen Namen `script_start` und `script_stop` in der [Konfiguration](../06-referenz/02-konfiguration.md) setzen.

## Benutzerfeld „Tunnel-Ziele“ an Sites fehlt in TRMM
Das Feld fehlt oder ist nicht an Sites angelegt. In der Einrichtung anlegen.

## Der API-Key darf Sites nicht ändern
Beim Speichern im Editor. Der Rolle fehlt `Manage Sites`. Recht ergänzen oder die Felder in TRMM selbst pflegen.

## HTTP 403 bei allen Abfragen
Der Key gehört nicht dem Benutzer mit der Rolle, oder der Benutzer ist deaktiviert. Siehe [TRMM-Rechte](../06-referenz/06-trmm-rechte.md).

## Ziel rot: nicht erreichbar
Der Tunnel steht, aber das Ziel antwortet nicht. Die Meldung lautet `<host>:<port> nicht erreichbar (SOCKS-Code n)`: Code 3 heißt Netz nicht erreichbar, 4 Host antwortet nicht, 5 Port geschlossen. Bei HTTPS-Problemen steht `https: SSLError` oder ähnlich da. Vom Agenten aus prüfen, z. B. in der TRMM-Shell mit `curl -kI https://192.168.1.1`. Liegt das Ziel in einem anderen VLAN, braucht der Agent Routing dorthin, oder ein anderer Agent im Feld **Tunnel-Agent**.

## Link auf ein anderes Gerät öffnet nicht
Der Verteiler lässt nur die Netze des Agenten und die eingetragenen Ziele durch. Liegt das andere Gerät in einem anderen Netz oder hat einen Hostnamen, es als Ziel eintragen.

## Kein Brave/Chromium gefunden
Der Client findet keinen Chromium-basierten Browser. Einen installieren oder den Pfad in `browser` setzen ([Konfiguration](../06-referenz/02-konfiguration.md)).
