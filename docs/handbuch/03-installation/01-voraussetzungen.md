---
title: Voraussetzungen
audience: Admin
outline: https://docs.bashclub.org/doc/voraussetzungen-e63pOmbH4J
outline_id: 0edcf799-3a7e-4555-a7b9-0bceb5aaeb20
---
## TRMM
- Die TRMM-API (z. B. `https://api.example.com`) muss für den Rechner des Technikers und für den Sprung-Host erreichbar sein. Steht sie hinter einer Allowlist, gehören beide hinein.
- Ein Adminkonto, um Rollen, Benutzer und API-Keys anzulegen.

## Agenten beim Kunden
In jeder Site, die erreichbar sein soll, braucht es mindestens einen Agenten unter **Linux oder macOS**, der online ist. Geeignet sind Server, die ohnehin laufen: Proxmox VE, eine Linux-VM, ein NAS mit TRMM-Agent, ein Raspberry Pi. Der Agent braucht:
- `bash`, `ssh` (OpenSSH-Client), `base64`, `mktemp`, `pkill`; auf üblichen Linux-Distributionen und macOS vorhanden
- ausgehend **TCP über IPv4** zum Sprung-Host auf dessen Port (Vorschlag 22222)
- Zugang zu den Zielen im Kundennetz, also im selben Netz oder mit Routing dorthin

Der Agent sieht vom Tunnel nichts außer dem `ssh`-Prozess während der Sitzung.

## Sprung-Host
- Linux-Server mit **Podman ab 4.4** (Quadlet) und systemd, z. B. Debian 12/13, Ubuntu 24.04, Fedora, RHEL 9
- ein TCP-Port, der aus dem Internet über **IPv4** erreichbar ist (direkt oder per Portweiterleitung), Vorschlag **22222**
- ausgehend HTTPS zur TRMM-API und für Paketupdates
- kaum Ressourcen: 1 vCPU, 512 MB RAM, 2 GB Platte reichen

Ein Sprung-Host gehört zu genau einem TRMM-Server. Er kann auf einem Host laufen, auf dem schon anderes läuft, z. B. neben TRMM. Siehe dazu den Hinweis zum Hairpin in [Eigenes Deployment](07-eigenes-deployment.md).

## Rechner des Technikers
- Linux, macOS oder Windows 10/11
- OpenSSH-Client (`ssh`, `ssh-keygen`); unter Windows 10/11 als optionales Feature enthalten
- Brave, Chromium, Google Chrome oder Microsoft Edge
- `git` für die Installation aus dem Repository, oder das Repository als Archiv
- Netzweg zum Sprung-Host und zur TRMM-API

Python muss nicht installiert sein; der Installer holt es über `uv`.
