---
title: CrowdSec
audience: Admin
outline:
outline_id:
---
Der Sprung-Host ist aus dem Internet erreichbar und bekommt Anmeldeversuche wie jeder SSH-Port. Seine Ablehnungen stehen als normale `sshd`-Zeilen im Journal, CrowdSec erkennt sie mit der Collection `crowdsecurity/sshd` ohne eigenen Parser.

| Logzeile | erkannt |
|---|---|
| `Invalid user … from …` (unbekanntes Konto) | ja |
| `Failed publickey for wr-tunnel from …` (falsches Zertifikat) | ja |
| `Connection closed by authenticating user wr-tunnel … [preauth]` (auch bei Absender ohne Freigabe) | ja |
| `Authentication tried … not from a permitted host` | nein, aber die Zeile danach zählt |

## Erfassung
Das Quadlet des Installers schreibt mit `LogDriver=journald` und `LogOpt=tag=sshd` ins Journal. Dort steht `SYSLOG_IDENTIFIER=sshd` und `CONTAINER_NAME=trmm-web-relay-jumphost`. Das `\r`, das `sshd` an seine Zeilen hängt, entfernt der Container bereits. Erfassung in CrowdSec, z. B. `/etc/crowdsec/acquis.d/trmm-web-relay.yaml`:
```yaml
source: journalctl
journalctl_filter:
  - CONTAINER_NAME=trmm-web-relay-jumphost
labels:
  type: syslog
```
`_SYSTEMD_UNIT` passt nicht, wenn der Container als Benutzerdienst läuft; `CONTAINER_NAME` passt immer.

## Agenten nicht sperren
Eine Sperre an der Firewall gilt meist für alle Dienste. Ein gesperrter Kunde verliert damit auch die Verbindung seiner Agenten zu TRMM. Ein Agent mit falscher Uhr oder ein abgebrochener Start kann aber durchaus ein paar abgelehnte Anmeldungen erzeugen.

Der Sprung-Host schreibt deshalb bei jedem Abgleich alle öffentlichen IPv4-Adressen der Agenten (auch der offline) in die Datei `export/agent-ipv4.txt` in seinem Volume. Diese Liste gehört in die Allowlist von CrowdSec. Pfad der Datei auf dem Host:
```bash
echo "$(podman volume inspect trmm-web-relay-jumphost --format '{{.Mountpoint}}')/export/agent-ipv4.txt"
```
Daraus z. B. per Timer eine Allowlist pflegen (CrowdSec mit zentralen Allowlists, `cscli allowlists`):
```bash
cscli allowlists create trmm-agents -d "TRMM-Agenten (TRMM Web-Relay)"
cscli allowlists add trmm-agents $(cat "$(podman volume inspect trmm-web-relay-jumphost --format '{{.Mountpoint}}')/export/agent-ipv4.txt")
```
Läuft CrowdSec auf einer anderen Maschine (z. B. der Firewall), die Datei dorthin übertragen.
