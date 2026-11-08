---
title: Glossar
audience: Anwender, Admin
outline: https://docs.bashclub.org/doc/glossar-E8DvalD4z3
outline_id: 860289dc-f87f-4c7f-8677-274cd22b6a3b
---
**Agent**: der TRMM-Agent auf einem Gerät beim Kunden. Für Web-Relay zählen Agenten unter Linux und macOS, die online sind.

**CA (Certificate Authority)**: ein SSH-Schlüsselpaar des Clients, mit dem er Zertifikate ausstellt. Je Client und TRMM-Server eine, im Schlüsselbund des Systems. Ihr öffentlicher Teil steht auf dem Sprung-Host in `TRUSTED_CA`.

**Client**: das Programm `trmm-web-relay` auf dem Rechner des Technikers, mit Steuerseite, SOCKS-Verteiler und Browserprofil.

**Einrichtung**: die Seite `http://127.0.0.1:8765/einrichtung` des Clients. Dort legt man Server an und prüft, was fehlt.

**Principal**: der Name, für den ein SSH-Zertifikat gilt. Agenten bekommen `site-<ID>`, Clients `wr-admin`.

**Reverse-SOCKS-Tunnel**: `ssh -R` ohne Zielangabe. Auf dem Sprung-Host entsteht ein Port, und jede Verbindung dorthin geht vom Agenten aus ins Kundennetz.

**Server**: in Web-Relay eine TRMM-Instanz mit ihrem Sprung-Host, ihrem API-Key und ihrer CA. Ein Client kann mehrere Server kennen, die Steuerseite zeigt einen.

**Site**: eine Site in TRMM (Kunde → Site). Ziele und Tunnel-Agenten stehen in Benutzerfeldern an der Site.

**Sitzung**: ein offener Tunnel zu einer Site, vom Verbinden bis zum Beenden.

**SOCKS-Verteiler**: ein lokaler SOCKS5-Proxy des Clients (`127.0.0.1:8766`). Er leitet Verbindungen des Browserprofils an die passende Sitzung und lehnt alles andere ab.

**Sprung-Host**: ein Container mit nur `sshd`, an dem sich Agenten und Clients treffen. Je TRMM-Server einer.

**Steuerseite**: die Startseite des Clients (`http://127.0.0.1:8765/`) mit den Sites des aktiven Servers.

**Tunnel-Agent**: Benutzerfeld an der Site mit den Hostnamen der Agenten, die den Tunnel bauen sollen, in der Reihenfolge der Priorität.

**Tunnel-Ziele**: Benutzerfeld an der Site mit den Websites, die der Client anbietet.
