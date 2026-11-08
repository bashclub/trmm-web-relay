# Sprung-Host

Der Sprung-Host ist ein Container-Image mit nur sshd (`jumphost/`). Agenten bauen dorthin den Tunnel auf, der Client verbindet sich dorthin. Er braucht einen von außen erreichbaren TCP-Port, Vorschlag 22222 (nur IPv4); im Container lauscht sshd auf 2222. Je TRMM-Server gibt es einen Sprung-Host.

## Anmeldung nur mit Zertifikaten

Der Sprung-Host kennt keine einzelnen Schlüssel, sondern vertraut nur den CAs der Clients (`TRUSTED_CA`). Für jede Sitzung erzeugt der Client zwei Wegwerf-Schlüssel und signiert sie für 15 Minuten:

| Konto | Wer | Principal im Zertifikat | darf |
|---|---|---|---|
| `wr-tunnel` | Tunnel-Skript auf dem Agenten | `site-<id>` | nur `127.0.0.1:<20000+id>` auf dem Sprung-Host öffnen (`-R`) |
| `wr-admin` | Client des Technikers | `wr-admin` | nur zu `127.0.0.1:*` weiterleiten (`-L`) |

Das Zertifikat gilt nur zum Anmelden. Der Tunnel läuft danach weiter, bis eine Seite ihn beendet. Ein abgegriffener Schlüssel ist nach 15 Minuten wertlos. Für eine neue Site muss am Sprung-Host nichts geändert werden.

Keine Shell, keine Befehle (`ForceCommand nologin`), keine Passwörter, kein root. Jede Anmeldung steht im Log (`LogLevel VERBOSE`), mit der Kennung des Zertifikats: Site, Agent, Sitzung und Techniker (`von=benutzer@rechner`).

**Absenderprüfung (nur IPv4):** Ein Zertifikat für `site-<id>` wird nur angenommen, wenn die Absenderadresse die öffentliche IPv4 eines Agenten dieser Site ist, der in TRMM gerade online ist, oder in einem festen Netz aus `ALLOW_FROM` liegt. Der Container fragt TRMM alle `REFRESH_SECONDS` (300) ab. Bei jeder Anmeldung gibt er die Regeln frisch aus (`AuthorizedPrincipalsCommand` mit `permitlisten` und `from`). Fehlt der Abgleich, bleibt die letzte Liste stehen. Abgelehnte Absender stehen im Log (`not from a permitted host`). Wechselt die Adresse eines Kunden (dynamische IP, CGNAT), geht es spätestens nach 5 min wieder.

**Clients** (`wr-admin`) kommen an alle Tunnel. `ADMIN_FROM` beschränkt sie auf die Netze der Techniker (VPN, Büro), zusätzlich zur Firewall. `wr-tunnel` muss aus dem Internet erreichbar sein. Rootless Podman mit pasta reicht die echte Absenderadresse durch.

**Mehrere Techniker:** Jeder Client hat je Server eine eigene CA. Alle CAs stehen in `TRUSTED_CA` (mit `;` getrennt). Der Installer fügt neue CAs hinzu und behält vorhandene. Einen Techniker sperren: seine Zeile aus `TRUSTED_CA` entfernen, Dienst neu starten.

## Installieren mit dem Installer

In der Einrichtung des Clients auf „Installer herunterladen“ klicken. Die Datei enthält das Image (Quellen), `install.sh` und die öffentlichen Werte (TRMM-Adresse, CA, Port). Auf dem Server mit Podman ab 4.4:

```sh
bash trmm-web-relay-sprunghost-<server>.sh            # installieren bzw. aktualisieren
bash trmm-web-relay-sprunghost-<server>.sh --help     # Werte und Optionen
bash trmm-web-relay-sprunghost-<server>.sh --uninstall
```

Läuft als root (Quadlet unter `/etc/containers/systemd`) oder als eigener Dienstbenutzer (rootless, `~/.config/containers/systemd`, `loginctl enable-linger`). Der Installer fragt nach:

- dem **TRMM-Key nur zum Lesen**: eigener TRMM-Benutzer, Rolle ohne Einschränkung auf Kunden, Rechte `List Clients` und `List Agents`. Er landet als Podman-Secret `trmm-web-relay-api-key`, nicht in Dateien.
- den **Netzen der Techniker** (`ADMIN_FROM`), leer heißt überall.

Er baut das Image, schreibt Einstellungen (`jumphost.env`) und Quadlet und startet den Dienst; systemd startet ihn beim Booten und nach Abstürzen neu. Am Ende zeigt er den Fingerabdruck des Host-Schlüssels, den der Client bei der Einrichtung zur Bestätigung anzeigt. Danach den Port in der Firewall freigeben bzw. weiterleiten.

**Auto-Update**: Der Installer legt die Quellen des Images unter `…/trmm-web-relay/src/` ab und richtet den Timer `trmm-web-relay-jumphost-update.timer` ein (sonntags 4–6 Uhr, holt Verpasstes nach). Der baut das Image ohne Cache mit frischer Debian-Basis und aktuellen Paketen neu und startet den Dienst nur, wenn sich installierte Pakete geändert haben. Von Hand: `bash …/trmm-web-relay/src/install.sh --update`. Abschalten: Installer mit `AUTO_UPDATE=0` erneut ausführen. Neue Fassungen des Sprung-Hosts selbst (sshd_config, Skripte) kommen weiter über einen neuen Installer aus dem Client.

## Umgebung

| Variable | Bedeutung |
|---|---|
| `TRUSTED_CA` | öffentliche CA-Schlüssel der Clients, mehrere mit `;` getrennt (Pflicht). Alternativ Dateien `/etc/trmm-web-relay/trusted_ca*.pub` |
| `TRMM_URL` | TRMM-API, z. B. `https://api.example.com` (Pflicht) |
| Secret, Datei `/run/secrets/trmm-api-key` | TRMM-Key nur zum Lesen, siehe oben (`TRMM_API_KEY_FILE` für einen anderen Pfad) |
| `ADMIN_FROM` | IPv4-Netze für Clients, mit Leerzeichen getrennt |
| `ALLOW_FROM` | feste IPv4-Netze, aus denen jede Site darf (Tests, eigenes RZ) |
| `REFRESH_SECONDS` | Abstand des TRMM-Abgleichs, Standard 300 |
| `REMOTE_PORT_BASE` | Port je Site = Basis + Site-ID, Standard 20000 (im Client gleich einstellen) |

Die Host-Schlüssel liegen im Volume `/var/lib/jumphost`. Sie bleiben über Neustarts und Updates erhalten; das Volume gehört in die Sicherung.

## Eigenes Deployment

Ohne Installer, z. B. mit Ansible: Image aus `jumphost/` bauen und als Quadlet starten. Für Sicherheitsupdates regelmäßig mit `podman build --pull=newer --no-cache` neu bauen und den Dienst neu starten (der Installer macht das mit seinem Timer).

```ini
[Container]
ContainerName=trmm-web-relay-jumphost
Image=localhost/trmm-web-relay-jumphost
PublishPort=22222:2222
EnvironmentFile=/etc/trmm-web-relay/jumphost.env
Secret=trmm-web-relay-api-key,target=trmm-api-key
Volume=trmm-web-relay-jumphost:/var/lib/jumphost:Z
RunInit=true
LogDriver=journald
LogOpt=tag=sshd

[Service]
Restart=always

[Install]
WantedBy=multi-user.target
```

`jumphost.env` im Format `KEY=Wert` ohne Anführungszeichen, Leerzeichen im Wert sind erlaubt:

```
TRMM_URL=https://api.example.com
TRUSTED_CA=ssh-ed25519 AAAA… trmm-web-relay-ca …;ssh-ed25519 AAAA… zweiter Techniker
ADMIN_FROM=203.0.113.7/32 10.8.0.0/24
```

Wer statt `EnvironmentFile=` einzelne `Environment=` nutzt: Werte mit Leerzeichen gehören samt Namen in Anführungszeichen (`Environment="ADMIN_FROM=a b"`), sonst übernimmt systemd nur das erste Netz.

Läuft der Sprung-Host auf demselben Host wie der Reverse-Proxy vor der TRMM-API, geht seine Abfrage über den öffentlichen Namen per Hairpin über die Firewall. Der Proxy sieht dann die Firewall als Absender und lehnt `/clients/` womöglich ab (403 bei einer Allowlist). Abhilfe: den Namen im Container auf den Host zeigen lassen, z. B. `AddHost=api.example.com:<Adresse>` und `Network=pasta:--map-host-loopback,<Adresse>`.

## CrowdSec

Die Ablehnungen stehen als normale sshd-Zeilen im Log. Die Collection `crowdsecurity/sshd` erkennt sie ohne eigenen Parser (geprüft mit `cscli explain`, damals noch mit einzelnen Schlüsseln; die Zeilen sind bei Zertifikaten gleich aufgebaut):

| Logzeile | erkannt |
|---|---|
| `Invalid user … from …` (unbekanntes Konto) | ja |
| `Failed publickey for wr-tunnel from …` (falsches Zertifikat) | ja |
| `Connection closed by authenticating user wr-tunnel … [preauth]` (auch bei Absender ohne Freigabe) | ja |
| `principals: Authentication tried … not from a permitted host` | nein, aber die Zeile danach zählt |

Damit CrowdSec die Zeilen findet:

- Quadlet mit `LogDriver=journald` und `LogOpt=tag=sshd`. Im Journal steht dann `SYSLOG_IDENTIFIER=sshd` und `CONTAINER_NAME=trmm-web-relay-jumphost`. Das `\r`, das sshd an seine Zeilen hängt, entfernt der Container bereits.
- Erfassung per `journalctl_filter: [CONTAINER_NAME=trmm-web-relay-jumphost]` mit `type: syslog`. `_SYSTEMD_UNIT` passt nicht, wenn der Container als Benutzerdienst läuft.

**Wichtig: Agenten nicht sperren.** Eine Sperre an der Firewall gilt meist für alle Dienste. Ein gesperrter Kunde verliert damit auch die Verbindung seiner Agenten zu TRMM. Der Container schreibt deshalb bei jedem Abgleich alle öffentlichen IPv4-Adressen der Agenten nach `/var/lib/jumphost/export/agent-ipv4.txt` (im Volume). Diese Liste gehört in die Allowlist von CrowdSec.

## Getestet (2026-11-06, lokal)

- Assistent gegen einen lokalen Sprung-Host und TRMM (nur lesend): Felder erkannt, veraltete Skripte erkannt, Host-Schlüssel bestätigt, Anmeldung mit Zertifikat, geänderter Host-Schlüssel nach Neuaufsetzen erkannt.
- Tunnel wie vom Agenten (`tunnel-start.sh` mit Zertifikat) und Weiterleitung wie vom Client: Die Seite kommt durch, Schlüssel und Zertifikat sind beim Agenten nach der Anmeldung gelöscht; `tunnel-stop.sh` beendet den Tunnel.
- Abgelehnt: Zertifikat für Site 2 auf dem Port von Site 1, unbekannter Principal, Site-Zertifikat als `wr-admin`, Client-Zertifikat als `wr-tunnel`, `-R` als `wr-admin`, Absender ohne Freigabe („not from a permitted host“).
- Installer: Env-Datei, Secret und Quadlet (`quadlet -dryrun`) korrekt; zweiter Lauf fügt eine CA hinzu und behält die erste sowie `ADMIN_FROM`. Start als Dienst mit systemd noch nicht auf einem echten Server ausprobiert.
