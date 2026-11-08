---
title: Vergleich mit VPN
audience: Anwender, Admin
outline: https://docs.bashclub.org/doc/vergleich-mit-vpn-q6RWXEuezN
outline_id: 62c983b1-c9a8-4082-812c-6f26b1da0dbe
---
Ein Mobile-VPN macht den Rechner des Technikers zum Teilnehmer im Kundennetz. Web-Relay öffnet auf Abruf einen schmalen, zeitbegrenzten Weg nur für den Browser, über einen Agenten, der in der Site schon läuft.

| | Mobile-VPN (z. B. WireGuard an der Kunden-Firewall) | TRMM Web-Relay |
|---|---|---|
| **Beim Kunden** | VPN-Server, offener Port, Profil je Techniker, Pflege je Kunde | nichts; der Agent baut nach außen auf, geht auch hinter CGNAT und ohne Portfreigabe |
| **Dauer** | Profil gilt dauerhaft | nur auf Klick, endet nach 30 min Leerlauf oder spätestens 4 h |
| **Zugangsdaten** | langlebige Schlüssel je Techniker und Kunde | Zertifikate für 15 Minuten; einen Techniker sperrt man an einer Stelle |
| **Was verbunden ist** | der ganze Rechner, alle Programme und Protokolle | nur das eigene Browserprofil |
| **Gleiche Adressbereiche** | Routing-Konflikte, also nur ein Kunde gleichzeitig | kein Routing auf dem Rechner, mehrere Kunden gleichzeitig |
| **Rechte auf dem Rechner** | VPN-Treiber, oft Adminrechte | keine, nur `ssh` und Browser |
| **Nachvollziehbarkeit** | Logs verstreut auf den VPN-Gateways der Kunden | TRMM-Audit-Log und Log des Sprung-Hosts mit Site, Agent, Techniker |
| **Berechtigung** | eigene Benutzerverwaltung je VPN | über TRMM: wer dort Skripte auf der Site starten darf |

## Wo ein VPN mehr kann
- **Protokolle**: Web-Relay transportiert nur TCP über SOCKS aus dem Browser. UDP, Ping, SMB, RDP oder SSH aus anderen Programmen gehen nicht.
- **Unabhängigkeit**: Web-Relay braucht TRMM, den Sprung-Host und einen Agenten unter Linux oder macOS, der online ist. Fällt einer aus, gibt es keinen Zugang. Ein VPN an der Firewall geht dann oft noch.
- **Leistung**: Alles läuft durch SSH über Agent und Sprung-Host. Für Weboberflächen reicht das, für große Dateiübertragungen eher nicht.

## Ehrlich zur Sicherheit
Web-Relay schafft kein neues Vertrauensverhältnis: Wer TRMM steuert, hat auf den Agenten ohnehin root. Technisch erreicht ein Tunnel jedes TCP-Ziel, das der Agent erreicht, so wie ein VPN. Der Gewinn: keine dauerhaft offenen Zugänge beim Kunden, keine langlebigen Schlüssel, jede Sitzung protokolliert.

Für Weboberflächen von Firewall, Hypervisor, NAS oder Router passt Web-Relay besser. Für Netzwerkarbeit mit allen Protokollen bleibt ein VPN das richtige Werkzeug. Es kann dann aus sein und nur im Bedarfsfall eingeschaltet werden, als Notweg, wenn TRMM ausfällt.
