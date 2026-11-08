---
title: Sicherung
audience: Admin
outline:
outline_id:
---
## Sprung-Host
Zu sichern:
- das Volume `trmm-web-relay-jumphost` mit dem Host-Schlüssel (sonst müssen alle Clients nach einer Neuinstallation einen neuen Fingerabdruck bestätigen),
- `/etc/trmm-web-relay/jumphost.env` mit `TRUSTED_CA` und den Netzen.

Volume sichern und zurückspielen:
```bash
podman volume export trmm-web-relay-jumphost -o /root/trmm-web-relay-jumphost.tar
```
```bash
podman volume create trmm-web-relay-jumphost
podman volume import trmm-web-relay-jumphost /root/trmm-web-relay-jumphost.tar
```
Das Image muss nicht gesichert werden, es entsteht neu aus den Quellen. Den TRMM-Key (Podman-Secret) fragt der Installer bei einer Neuinstallation erneut ab.

## Client
Nichts davon ist unersetzlich:
- `~/.config/trmm-web-relay/config.toml`: Server und Einstellungen, ohne Geheimnisse
- Schlüsselbund bzw. `~/.local/share/trmm-web-relay/secrets/`: API-Keys und CA
- `~/.local/share/trmm-web-relay/known_hosts`: bestätigte Host-Schlüssel

Geht ein Rechner verloren, richtet man den Client neu ein und trägt die neue CA beim Sprung-Host ein; die alte entfernt man ([Zugang entziehen](04-zugang-entziehen.md)). Die CA bewusst nicht auf andere Rechner kopieren: Jede Kopie ist ein weiterer Schlüssel zu allen Sites dieses Servers.

## TRMM
Ziele und Tunnel-Agenten stehen in TRMM und sind mit dessen Sicherung gesichert.
