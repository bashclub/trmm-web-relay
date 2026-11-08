---
title: Ablauf einer Sitzung
audience: Admin
outline:
outline_id:
---
Eine Sitzung verbindet den Browser des Technikers mit dem Netz einer Site. Sie besteht aus zwei SSH-Verbindungen, die sich auf dem Sprung-Host treffen.

```
Browserprofil ─► SOCKS-Verteiler ─► ssh -L ─►  Sprung-Host  ◄─ ssh -R ◄─ Agent ─► Ziel im Kundennetz
 (Techniker)      127.0.0.1:8766     wr-admin   127.0.0.1:20000+Site   wr-tunnel          192.168.1.1
```

## Start
1. **Verbinden** auf der Steuerseite. Der Client liest die Agenten der Site aus TRMM und wählt einen: den ersten aus dem Feld **Tunnel-Agent**, der online ist und Linux oder macOS hat; sonst einen solchen Agenten der Site, Server vor Workstations.
2. Der Client erzeugt zwei Wegwerf-Schlüssel und signiert sie mit seiner CA für 15 Minuten: einen für den Agenten (Principal `site-<ID>`), einen für sich selbst (`wr-admin`). Die Kennung im Zertifikat nennt Site, Agent, Sitzung und Techniker.
3. Der Client startet über die TRMM-API das Skript **Web-Relay: Tunnel starten** auf dem Agenten, im Modus „nicht warten“ und mit der Höchstdauer als Laufzeitgrenze. Schlüssel, Zertifikat und Host-Schlüssel des Sprung-Hosts gehen als Umgebungsvariablen mit, nicht als Argumente.
4. Das Skript meldet sich als `wr-tunnel` am Sprung-Host an und öffnet dort `127.0.0.1:<20000 + Site-ID>` als Reverse-SOCKS-Proxy (`ssh -R` ohne Ziel). Den Schlüssel löscht es direkt nach der Anmeldung.
5. Der Client meldet sich als `wr-admin` an und verbindet einen freien lokalen Port mit diesem Port (`ssh -L`). Er wartet bis zu 90 Sekunden, bis der Tunnel antwortet.
6. Der Client schaltet im SOCKS-Verteiler frei: die privaten IPv4-Netze des Agenten (ab /16, z. B. `192.168.1.0/24`), die IP-Adressen der Ziele und ihre Hostnamen.
7. Er prüft jedes Ziel: HTTPS oder HTTP, Seitentitel als Name, falls keiner eingetragen ist. Das Ergebnis merkt er sich für das nächste Mal.

## Während der Sitzung
Das Browserprofil schickt jede Verbindung an den SOCKS-Verteiler. Der sucht die Sitzung, zu der das Ziel gehört, und leitet weiter; alles andere lehnt er ab. Gehört eine Adresse zu zwei Sitzungen (z. B. `192.168.1.1` bei zwei Kunden), gewinnt das genauere Netz und bei Gleichstand die neuere Sitzung. Jede Verbindung zählt als Aktivität.

## Ende
Eine Sitzung endet durch:
- **Beenden** auf der Steuerseite oder Beenden des Clients,
- **Leerlauf**: 30 Minuten ohne Verbindung über den Verteiler (`idle_minutes`),
- **Höchstdauer**: 4 Stunden (`max_hours`),
- **Abbruch** einer der SSH-Verbindungen.

Der Client startet dann **Web-Relay: Tunnel stoppen** auf dem Agenten, das genau den ssh-Prozess dieser Sitzung beendet, und schließt seine eigene Verbindung. Fällt der Client aus, endet der Tunnel trotzdem: TRMM beendet das Skript nach der Laufzeitgrenze, und der Sprung-Host trennt eine Seite ohne Gegenstelle nach etwa 45 Sekunden.

## Was dabei in TRMM steht
Jeder Start und jedes Stoppen ist ein Skriptlauf im Verlauf des Agenten und im Audit-Log, mit dem TRMM-Benutzer, dem der API-Key gehört. Die Argumente zeigen Sitzung, Sprung-Host und Port.
