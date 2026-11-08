# ADR 0001: Aufbau

Status: angenommen (2026-11-05), ergänzt durch ADR 0002 und ADR 0003

## Kontext

Viele MSPs halten zu ihren Kunden dauerhafte VPN-Tunnel, über die sie jederzeit in die Kundennetze kommen. Das ist eine große Angriffsfläche. Tactical RMM (TRMM) deckt Shell, Desktop und VNC bereits ab, und zwar ohne Tunnel (der Agent verbindet sich von innen). Es fehlt nur der Zugriff auf **Weboberflächen im Kundennetz** (Firewall, Switches, Drucker, Appliances), auch auf Geräten ohne Agent.

Anforderungen:

- Zugriff nur für die Dauer der Nutzung, danach ist nichts mehr offen.
- **Ein Schritt** bis zur Seite beim Kunden, im normalen Browser.
- Auf macOS und Linux, Windows später.

Verworfen:

- **RPort**: Open-Source-Version 2023 eingestellt, Fork OpenRPort wenig gepflegt.
- **MeshCentral**: TRMM baut eine eigene Fernsteuerung und löst sich davon.
- **Teleport, zrok/OpenZiti**: ein weiteres großes System mit eigenem Agenten bei jedem Kunden, für eine einzige Lücke zu viel.
- **Web-Portal mit Reverse-Proxy (Caddy)**: viele Appliance-Oberflächen vertragen keinen Reverse-Proxy (absolute Weiterleitungen auf ihre IP, Websockets, Prüfung des Host-Headers).
- **SSH-Tunnel von Hand**: zu umständlich (3–5 Schritte).

## Entscheidung

### Ablauf

1. Der Techniker öffnet die lokale Steuerseite (`http://localhost:8765`) und wählt eine Site, z. B. „Musterkunde → Zentrale“.
2. Der Client startet über die TRMM-API das Tunnel-Skript auf einem Agenten dieser Site, der gerade online ist (bevorzugt das Gerät aus dem Feld „Tunnel-Agent“, sonst ein Server).
3. Das Skript baut einen **Reverse-SOCKS-Tunnel** zum Sprung-Host auf (`ssh -N -R 127.0.0.1:<port>`, ohne Zielangabe = SOCKS-Proxy ins Kundennetz).
4. Der Client verbindet per SSH einen lokalen Port mit diesem Tunnel und schaltet die Ziele und das Netz der Site in seinem SOCKS-Verteiler frei.
5. Der Browser öffnet die **echte Adresse** des Ziels (z. B. `https://192.168.10.1`) in einem neuen Tab. Navigieren auf der Seite, Weiterleitungen und Websockets laufen mit, weil der ganze Host bzw. das ganze Netz durch den Tunnel geht.
6. Ende: Klick auf „Beenden“, nach 30 Minuten Leerlauf oder spätestens nach 4 Stunden. Der Client ruft dafür das Stopp-Skript über TRMM auf; die Höchstdauer setzt zusätzlich TRMM mit der Laufzeitgrenze des Skripts durch, der Sprung-Host trennt Sitzungen ohne Gegenstelle (`ClientAliveInterval`).

### Bausteine

- **Sprung-Host**: Container mit nur sshd (`jumphost/`), je TRMM-Server einer, von außen auf einem TCP-Port erreichbar (Vorschlag 22222). Konten dürfen nur Weiterleitungen auf `127.0.0.1` öffnen: keine Shell, keine Verbindungen ins Netz. Jede Sitzung steht mit Site, Beginn und Ende im Log. (Seit ADR 0002: Zertifikate statt Schlüssel je Site.)
- **TRMM-Skripte** „Tunnel starten“ und „Tunnel stoppen“ (Shell für Linux und macOS, PowerShell für Windows später), mit Laufzeitgrenze und Kennung im Aufruf, damit genau dieser Prozess beendet wird. Wer wann wo gestartet hat, steht in TRMM.
- **Ziele** als Benutzerfeld „Tunnel-Ziele“ an der Site (`[Name |] host:port` oder URL, getrennt mit `;`), dazu „Tunnel-Agent“ als Prioritätsliste. Ohne Protokoll erkennt der Client selbst, ob `https` oder `http` antwortet; ohne Name nimmt er den Seitentitel. Kein zweites Inventar.
- **Client** in Python, verteilt mit `uv tool install`:
  - TRMM-API (Inventar, Online-Status, Ziele, Skripte starten und stoppen),
  - SSH zum Sprung-Host,
  - Steuerseite und SOCKS-Verteiler auf `localhost`,
  - Geheimnisse (TRMM-API-Key, CA) im Schlüsselbund des Systems.
- **Eigenes Browserprofil** (Brave bzw. Chromium, statt PAC-Datei im System): Der Client startet ein eigenes Profil mit `--proxy-server` auf seinen SOCKS-Verteiler und `--ignore-certificate-errors`, damit selbstsignierte Zertifikate nicht stören. Der Verteiler lässt nur Ziele und Netze aktiver Sitzungen durch und lehnt alles andere ab; das Profil kommt also nicht ins Internet, und das normale Surfen bleibt unberührt. Bei gleicher IP bei zwei Kunden gewinnt die neuere Sitzung. (Seit ADR 0003: Zertifikate werden geprüft, Web Store und `direct_hosts` direkt erreichbar.)

### Notweg

Fällt TRMM oder der Sprung-Host aus, braucht es einen anderen Weg ins Kundennetz, z. B. einen VPN-Zugang an der Kunden-Firewall, der normalerweise **aus** ist und nur im Notfall eingeschaltet wird. Er gehört regelmäßig getestet. Das ist nicht Teil dieses Projekts.

## Folgen

- Kein Kundennetz muss mehr dauerhaft vom MSP aus erreichbar sein.
- TRMM wird zum Schlüssel für den Zugang; Härtung von TRMM (2FA, Weboberfläche nur aus Allowlist bzw. VPN, Updates) bekommt höhere Priorität.
- Der Client braucht einen TRMM-API-Key mit dem Recht „Run Scripts“, abgelegt im Schlüsselbund.
- Offen: Windows-Agenten (PowerShell-Skript), Einschränkung auf einzelne Ziele über die Firewall am Kundengerät.
