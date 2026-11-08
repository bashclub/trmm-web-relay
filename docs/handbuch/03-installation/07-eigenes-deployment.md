---
title: Eigenes Deployment des Sprung-Hosts
audience: Admin
outline: https://docs.bashclub.org/doc/eigenes-deployment-des-sprung-hosts-wgXlE9j6Ql
outline_id: 46a98659-391b-467b-a3cd-9598dc01bc71
---
Wer Server mit Ansible, Salt oder eigenen Quadlets verwaltet, braucht den Installer nicht. Das Image entsteht aus dem Ordner `jumphost/` im Repository, die Einstellungen kommen per Umgebung.

## Image bauen
```bash
git clone https://code.bashclub.org/bashclub/trmm-web-relay.git
podman build --pull=newer -t localhost/trmm-web-relay-jumphost trmm-web-relay/jumphost
```

## Secret anlegen
Den Lese-Key ([TRMM vorbereiten](02-trmm-vorbereiten.md)) ohne Echo einlesen und als Secret ablegen:
```bash
read -rs key && printf '%s' "$key" | podman secret create trmm-web-relay-api-key - && unset key
```

## Einstellungen
`/etc/trmm-web-relay/jumphost.env`, Format `KEY=Wert` ohne Anführungszeichen, Leerzeichen im Wert sind erlaubt:
```
TRMM_URL=https://api.example.com
TRUSTED_CA=ssh-ed25519 AAAA… trmm-web-relay-ca msp anna@laptop;ssh-ed25519 AAAA… trmm-web-relay-ca msp ben@pc
ADMIN_FROM=203.0.113.7/32 10.8.0.0/24
```
Die CA-Zeilen stehen in der Einrichtung jedes Clients unter **CA dieses Clients** (Knopf **Kopieren**). Alle Variablen: [Umgebung des Sprung-Hosts](../06-referenz/04-umgebung-sprunghost.md).

Wer statt `EnvironmentFile=` einzelne `Environment=` nutzt: Werte mit Leerzeichen gehören samt Namen in Anführungszeichen (`Environment="ADMIN_FROM=a b"`), sonst übernimmt systemd nur das erste Netz.

## Quadlet
`/etc/containers/systemd/trmm-web-relay-jumphost.container`:
```ini
[Unit]
Description=TRMM Web-Relay Sprung-Host
After=network-online.target
Wants=network-online.target

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
```bash
systemctl daemon-reload
systemctl start trmm-web-relay-jumphost.service
```
`RunInit=true` sorgt dafür, dass beendete Prozesse im Container aufgeräumt werden. `LogDriver=journald` mit `tag=sshd` braucht [CrowdSec](../05-betrieb/03-crowdsec.md). Das Volume enthält den Host-Schlüssel und gehört in die Sicherung.

## Updates
Für Sicherheitsupdates das Image regelmäßig ohne Cache neu bauen und den Dienst neu starten, am besten nur, wenn sich Pakete geändert haben. Der Installer macht das mit `install.sh --update`: Image als `:candidate` bauen, Paketlisten mit `dpkg-query -W` vergleichen, nur bei Unterschieden umtaggen und neu starten. Diesen Ablauf kann man in eine eigene Rolle übernehmen.

## Hairpin: Sprung-Host neben TRMM
Läuft der Sprung-Host auf demselben Host wie der Reverse-Proxy vor der TRMM-API, geht seine Abfrage über den öffentlichen Namen per Hairpin über die Firewall. Der Proxy sieht dann die Firewall als Absender und lehnt `/clients/` womöglich ab (403 bei einer Allowlist). Abhilfe: den Namen im Container auf den Host zeigen lassen, z. B. im Quadlet
```ini
AddHost=api.example.com:192.0.2.10
Network=pasta:--map-host-loopback,192.0.2.10
```
Verbindungen des Containers an diese Adresse landen auf dem Loopback des Hosts (`127.0.0.1`); der Proxy muss dort lauschen. Die Adresse ist frei gewählt und sollte sonst nicht vorkommen.
