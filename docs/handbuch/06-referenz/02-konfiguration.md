---
title: Konfiguration des Clients
audience: Admin
outline: https://docs.bashclub.org/doc/konfiguration-des-clients-MKKWxLCIMA
outline_id: d96ef93e-fdbb-4380-be86-285833adedc5
---
Die Einstellungen stehen in `~/.config/trmm-web-relay/config.toml` (anderer Pfad mit der Umgebungsvariable `TRMM_WEB_RELAY_CONFIG`). Die Einrichtung schreibt die Datei; von Hand braucht man sie nur für die selteneren Einstellungen. Geheimnisse stehen nie darin. Die Datei enthält nur Werte, die vom Standard abweichen. Nach einer Änderung von Hand den Client neu starten.

```toml
idle_minutes = 60
active_server = "mein-msp"

[[server]]
id = "mein-msp"
name = "Mein MSP"
trmm_url = "https://api.example.com"
jump = "relay.example.com:22222"
```

## Übersicht
| Einstellung | Standard | Bedeutung |
|---|---|---|
| `control_port` | `8765` | Port der Steuerseite |
| `socks_port` | `8766` | Port des SOCKS-Verteilers |
| `idle_minutes` | `30` | Leerlauf bis zum Ende einer Sitzung |
| `max_hours` | `4` | Höchstdauer einer Sitzung |
| `browser` | leer | Pfad zum Browser |
| `direct_hosts` | leer | Hosts, die das Profil direkt erreicht |
| `extension_store` | `true` | Web Store und Updates für Erweiterungen erreichbar |
| `ignore_cert_errors` | `false` | Zertifikatsfehler im Profil ignorieren |
| `update_url` | `pyproject.toml` auf `main` | Quelle für den Hinweis auf neue Versionen |
| `active_server` | leer | Server, den die Steuerseite zeigt |
| `id` | – | Kennung des Servers (Pflicht) |
| `name` | `id` | Anzeigename |
| `trmm_url` | – | Adresse der TRMM-API (Pflicht) |
| `jump` | leer | Sprung-Host als `host:port` |
| `remote_port_base` | `20000` | Basis der Tunnel-Ports |
| `field_targets` | `Tunnel-Ziele` | Name des Felds mit den Zielen |
| `field_agents` | `Tunnel-Agent` | Name des Felds mit den Tunnel-Agenten |
| `script_start` | `Web-Relay: Tunnel starten` | Name des Start-Skripts in TRMM |
| `script_stop` | `Web-Relay: Tunnel stoppen` | Name des Stopp-Skripts in TRMM |

## Allgemein
### `control_port`
Port der Steuerseite auf `127.0.0.1`. Ändern, wenn 8765 belegt ist. Er dient auch dazu, einen laufenden Client zu erkennen.

### `socks_port`
Port des SOCKS-Verteilers auf `127.0.0.1`, an den das Browserprofil alle Verbindungen schickt.

### `idle_minutes`
Minuten ohne Verbindung durch den Tunnel, nach denen eine Sitzung endet.

### `max_hours`
Stunden, nach denen eine Sitzung spätestens endet. Gilt auch als Laufzeitgrenze des Start-Skripts in TRMM: Selbst wenn der Client ausfällt, beendet der Agent den Tunnel danach.

### `browser`
Pfad zu einem Chromium-basierten Browser. Leer: Der Client sucht Brave, Chromium, Google Chrome und (unter Windows) Microsoft Edge, in dieser Reihenfolge. Firefox geht nicht, weil der Client die Chromium-Schalter für Profil und Proxy nutzt.

### `direct_hosts`
Ab 0.3, ab 0.4 auch in der Einrichtung unter **Browserprofil**. Liste von Hosts, die das Browserprofil direkt ins Internet erreicht, ohne Tunnel, z. B. der Server eines Passwortmanagers. Ein Eintrag gilt für den Host und alle Subdomains, nur auf Port 443; ein anderer Port steht dahinter:
```toml
direct_hosts = ["bitwarden.eu", "vault.example.com:8443"]
```
Sitzungen haben Vorrang: Ist ein Host zugleich Ziel einer offenen Sitzung, geht er durch den Tunnel. Verbindungen zu diesen Hosts zählen nicht als Aktivität einer Sitzung. Welche Hosts das Profil vergeblich aufrufen wollte, steht im Log (`abgelehnt …`). Nur vertrauenswürdige Hosts eintragen: Jede Seite, die das Profil laden kann, könnte Anfragen an die Geräte in offenen Tunneln schicken. Siehe [Erweiterungen und Passwortmanager](../04-bedienung/05-erweiterungen.md).

### `extension_store`
Ab 0.3. `true`: Das Profil erreicht den Chrome Web Store und die Download- und Update-Server für Erweiterungen von Chrome, Brave und Edge. `false`: Erweiterungen lassen sich weder installieren noch aktualisieren.

### `ignore_cert_errors`
Ab 0.3. `true`: Das Profil startet mit `--ignore-certificate-errors` und zeigt keine Zertifikatswarnungen, so wie bis 0.2. Das gilt dann auch für `direct_hosts` und den Web Store: Wer im Netz des Technikers mitliest, könnte sich etwa als Server des Passwortmanagers ausgeben. Darum `false` lassen, wenn `direct_hosts` gesetzt ist. Die Änderung wirkt erst, wenn alle Fenster des Profils geschlossen waren.

### `update_url`
Ab 0.4. Adresse einer `pyproject.toml`, aus der der Client die neueste Version liest: beim Start und danach einmal am Tag, mit dem Ergebnis im Cache (`~/.cache/trmm-web-relay/version.json`). Standard: `https://code.bashclub.org/bashclub/trmm-web-relay/raw/branch/main/pyproject.toml`. Wer einen eigenen Fork verteilt, trägt dessen Datei ein. Leer (`update_url = ""`): keine Abfrage, kein Hinweis. Die Abfrage schickt nur die installierte Version im User-Agent mit.

### `active_server`
`id` des Servers, den die Steuerseite zeigt. Setzt die Auswahl oben auf der Steuerseite. Leer oder unbekannt: der erste Server.

## Je Server (`[[server]]`)
### `id`
Kurze Kennung aus `a-z`, `0-9` und `-`, höchstens 32 Zeichen, eindeutig. Sie steckt in den Namen der Geheimnisse im Schlüsselbund (`trmm-web-relay-<id>-api-key`, `trmm-web-relay-<id>-ca`) und im Dateinamen des Installers. Die Einrichtung bildet sie aus dem Namen; nachträglich ändern heißt, Key und CA neu anzulegen.

### `name`
Anzeigename in Steuerseite und Einrichtung.

### `trmm_url`
Adresse der TRMM-API, z. B. `https://api.example.com`, ohne `/` am Ende.

### `jump`
Sprung-Host als `host:port`, so wie Agenten und dieser Rechner ihn erreichen. Ohne Port gilt 22222. IPv6-Adressen in eckigen Klammern.

### `remote_port_base`
Port je Site auf dem Sprung-Host = Basis + Site-ID. Muss zu `REMOTE_PORT_BASE` am Sprung-Host passen ([Umgebung des Sprung-Hosts](04-umgebung-sprunghost.md)).

### `field_targets`
Name des Benutzerfelds an Sites mit den Zielen. Nur ändern, wenn das Feld in TRMM anders heißen soll; die Einrichtung legt es mit diesem Namen an.

### `field_agents`
Name des Benutzerfelds an Sites mit den Tunnel-Agenten.

### `script_start`
Name des Start-Skripts in TRMM.

### `script_stop`
Name des Stopp-Skripts in TRMM.

## Umgebungsvariablen
| Variable | Bedeutung |
|---|---|
| `TRMM_WEB_RELAY_CONFIG` | anderer Pfad der Konfiguration |
| `TRMM_WEB_RELAY_SECRETS_DIR` | Ordner für Geheimnisse ohne Schlüsselbund, Standard `~/.local/share/trmm-web-relay/secrets` |
