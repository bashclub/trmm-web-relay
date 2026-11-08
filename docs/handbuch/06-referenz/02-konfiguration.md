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
