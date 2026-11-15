---
title: Felder an der Site
audience: Admin
outline: https://docs.bashclub.org/doc/felder-an-der-site-kafsV3DWIm
outline_id: 603f30cc-352b-48c4-a7f1-fc456edb86a0
---
Beide Felder sind Benutzerfelder (Custom Fields) an der **Site**, Typ **Text**. Die Steuerseite schreibt sie im passenden Format ([Sites bearbeiten](../04-bedienung/03-sites-bearbeiten.md)); dieses Format gilt, wenn man sie in TRMM oder per API selbst pflegt.

## Tunnel-Ziele
Einträge, getrennt mit `;` oder Zeilenumbruch. Je Eintrag:
```
[Name |] Adresse
```
- **Name** (optional): Text des Links, ohne `|` und `;`. Ohne Name nimmt der Client den Seitentitel.
- **Adresse**: eine URL mit `http://`, `https://` oder (ab 0.6) `ssh://[benutzer@]host[:port]`, oder nur `host[:port][/pfad]`.

| Adresse | Der Client probiert |
|---|---|
| `192.168.1.1` | `https://192.168.1.1/`, dann `http://192.168.1.1/` |
| `192.168.1.1:8443` | HTTPS auf 8443, dann HTTP auf 8443, dann SSH auf 8443 |
| `https://192.168.1.1:8443/ui/` | nur diese URL |
| `nas.local:5001` | HTTPS, dann HTTP auf 5001, dann SSH; `nas.local` löst der Agent auf |
| `192.168.1.10:22` | nur SSH |
| `ssh://admin@192.168.1.10` | nur SSH auf Port 22, als Benutzer `admin` |

Beispiel:
```
OPNsense | 192.168.1.1:8443; Proxmox | 192.168.1.2:8006; https://nas.local:5001/; Drucker | 192.168.1.50; Switch | ssh://admin@192.168.1.3
```
SSH ohne Port oder `ssh://` erkennt der Client nicht, weil er ohne Port nur 443 und 80 probiert. Bei `ssh://` sind ein Benutzer, aber kein Passwort und kein Pfad erlaubt. Andere Protokolle als HTTP, HTTPS und SSH lehnt der Client ab. Einträge, die er nicht versteht, zeigt die Steuerseite unter **Nicht lesbar** und `trmm-web-relay targets` mit `!`; die übrigen gehen trotzdem.

Hostnamen löst der Agent auf, nicht der Rechner des Technikers (SOCKS mit Namensauflösung am Ende des Tunnels). Ein Hostname ist im Tunnel nur erreichbar, wenn er als Ziel eingetragen ist; IP-Adressen auch, wenn sie in einem Netz des Agenten liegen.

## Tunnel-Agent
Hostnamen von Agenten der Site, getrennt mit `;`, `,` oder Leerzeichen, in der Reihenfolge der Priorität, Groß- und Kleinschreibung egal:
```
pve01; nas01
```
Der Client nimmt den ersten, der in TRMM online ist und Linux oder macOS hat. Sonst nimmt er einen anderen Agenten der Site, der online ist und Linux oder macOS hat, Server vor Workstations, alphabetisch. Hostnamen, die es in der Site nicht gibt, überspringt er mit einem Hinweis. Das Feld darf leer sein oder fehlen.
