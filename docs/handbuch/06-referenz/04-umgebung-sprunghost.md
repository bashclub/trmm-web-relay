---
title: Umgebung des Sprung-Hosts
audience: Admin
outline: https://docs.bashclub.org/doc/umgebung-des-sprung-hosts-6JjCNACzfn
outline_id: 2cd76c94-3e0f-46b6-9bf0-395387be916a
---
Der Container des Sprung-Hosts wird nur über Umgebungsvariablen eingestellt. Der Installer schreibt sie nach `jumphost.env`; bei [eigenem Deployment](../03-installation/07-eigenes-deployment.md) setzt man sie selbst. Änderungen wirken nach einem Neustart des Dienstes.

| Variable | Standard | Bedeutung |
|---|---|---|
| `TRUSTED_CA` | – | öffentliche CA-Schlüssel der Clients, mehrere mit `;` getrennt (Pflicht). Zusätzlich liest der Container Dateien `/etc/trmm-web-relay/trusted_ca*.pub`, falls eingehängt |
| `TRMM_URL` | – | TRMM-API, z. B. `https://api.example.com` (Pflicht) |
| `TRMM_API_KEY_FILE` | `/run/secrets/trmm-api-key` | Datei mit dem TRMM-Key nur zum Lesen; normalerweise das Podman-Secret `trmm-web-relay-api-key` |
| `ADMIN_FROM` | leer | IPv4-Netze, aus denen sich Clients (`wr-admin`) anmelden dürfen, mit Leerzeichen getrennt. Leer: von überall |
| `ALLOW_FROM` | leer | feste IPv4-Netze, aus denen sich jede Site anmelden darf, mit Leerzeichen getrennt, z. B. für Tests oder ein eigenes Rechenzentrum |
| `REFRESH_SECONDS` | `300` | Abstand des Abgleichs mit TRMM in Sekunden |
| `SSH_PORT` | `2222` | Port von `sshd` im Container |
| `REMOTE_PORT_BASE` | `20000` | Port je Site auf `127.0.0.1` im Container = Basis + Site-ID; im Client `remote_port_base` gleich setzen |

`PUBLIC_PORT` in `jumphost.env` benutzt nur der Installer für das Quadlet (`PublishPort=<PUBLIC_PORT>:2222`); der Container selbst liest ihn nicht.

## Volume
`/var/lib/jumphost` im Container, beim Installer das Volume `trmm-web-relay-jumphost`:
| Pfad | Inhalt |
|---|---|
| `ssh_host_ed25519_key`, `.pub` | Host-Schlüssel, beim ersten Start erzeugt |
| `export/agent-ipv4.txt` | öffentliche IPv4-Adressen aller Agenten, für eine Allowlist ([CrowdSec](../05-betrieb/03-crowdsec.md)) |

## Konten und Ports
| Konto | Anmeldung mit | darf |
|---|---|---|
| `wr-tunnel` | Zertifikat mit Principal `site-<ID>`, nur von Absendern der Site oder aus `ALLOW_FROM` | `-R 127.0.0.1:<REMOTE_PORT_BASE + ID>` |
| `wr-admin` | Zertifikat mit Principal `wr-admin`, nur aus `ADMIN_FROM` | `-L` zu `127.0.0.1:*` |

Keine Shell (`ForceCommand nologin`), kein TTY, keine Passwörter, kein root, keine Agent- oder X11-Weiterleitung. Nur IPv4 (`AddressFamily inet`). Verbindungen ohne Gegenstelle trennt `sshd` nach etwa 45 Sekunden (`ClientAliveInterval 15`, `ClientAliveCountMax 3`).
