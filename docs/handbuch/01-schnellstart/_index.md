---
title: Schnellstart
audience: Admin
outline:
outline_id:
---
Diese Anleitung führt in sechs Schritten zur ersten Weboberfläche beim Kunden. Sie setzt eine laufende TRMM-Instanz voraus, Adminrechte darin und einen Linux-Server mit Podman, der aus dem Internet auf einem TCP-Port erreichbar ist. Hintergründe stehen im [Konzept](../02-konzept/_index.md), Einzelheiten zu jedem Schritt in [Installation und Einrichtung](../03-installation/_index.md).

## Was du brauchst
- **TRMM** mit API-Adresse (z. B. `https://api.example.com`) und einem Adminkonto.
- **Einen Agenten unter Linux oder macOS** an der Site, die du erreichen willst, der online ist (Server bevorzugt). Er braucht `ssh` und muss TCP zum Sprung-Host nach außen aufbauen dürfen.
- **Einen Sprung-Host**: Linux-Server mit Podman ab 4.4 und einer öffentlichen IPv4-Adresse oder Portweiterleitung, z. B. eine kleine VM im Rechenzentrum oder hinter der eigenen Firewall.
- **Den Rechner des Technikers** (Linux, macOS oder Windows) mit OpenSSH-Client und Brave, Chromium, Chrome oder Edge.

## 1. TRMM: Benutzer und Key für den Client
In TRMM unter **Settings → Permissions Manager** eine Rolle `web-relay` anlegen, ohne Einschränkung auf Kunden, mit den Rechten:
- `List Clients`, `List Agents`, `View Custom Fields`, `List Scripts`, `Run Scripts`
- für die Einrichtung und zum Bearbeiten der Ziele zusätzlich `Manage Custom Fields`, `Manage Scripts` und `Manage Sites`

Dann unter **Settings → User Administration** einen Benutzer für den Techniker mit dieser Rolle anlegen (Dashboard-Anmeldung darf gesperrt sein) und unter **Settings → Global Settings → API Keys** einen Key **für diesen Benutzer** erzeugen. Der Key gehört zum Benutzer: Es zählen die Rechte von dessen Rolle.

Für den Sprung-Host einen zweiten Benutzer mit einer Rolle nur zum Lesen anlegen (`List Clients`, `List Agents`) und auch dafür einen Key erzeugen.

## 2. Client installieren
Linux und macOS:
```bash
git clone https://code.bashclub.org/bashclub/trmm-web-relay.git
sh trmm-web-relay/install/client.sh
```
Windows (PowerShell):
```powershell
git clone https://code.bashclub.org/bashclub/trmm-web-relay.git
powershell -ExecutionPolicy Bypass -File trmm-web-relay\install\client.ps1
```
Der Installer holt bei Bedarf `uv` (bringt Python mit), installiert den Client und legt das Symbol **TRMM Web-Relay** auf dem Desktop und im Startmenü an.

## 3. Server in der Einrichtung anlegen
Doppelklick auf **TRMM Web-Relay**. Beim ersten Start öffnet sich die Einrichtung in einem eigenen Browserfenster. Eintragen:
- **Name**: z. B. der Name deines MSP
- **TRMM-API-Adresse**: `https://api.example.com`
- **API-Key**: der Key aus Schritt 1 (landet im Schlüsselbund)
- **Sprung-Host**: `relay.example.com:22222` (Name oder IP, unter der Agenten und dein Rechner den Sprung-Host erreichen)

**Speichern und prüfen** zeigt eine Liste. Die Punkte mit Knopf der Reihe nach erledigen:
1. Felder **Tunnel-Ziele** und **Tunnel-Agent** an Sites: **In TRMM anlegen**
2. Skripte **Web-Relay: Tunnel starten** und **Web-Relay: Tunnel stoppen**: **In TRMM anlegen**
3. **CA dieses Clients**: **CA erzeugen**

Jeder Knopf, der in TRMM schreibt, fragt vorher nach.

## 4. Sprung-Host installieren
In der Einrichtung unter **Sprung-Host installieren oder aktualisieren** den Installer herunterladen und auf den Server kopieren. Dort als root ausführen:
```bash
bash trmm-web-relay-sprunghost-*.sh
```
Er fragt nach dem Lese-Key aus Schritt 1 und den IPv4-Netzen, aus denen sich Techniker anmelden (leer: überall). Am Ende zeigt er den **Fingerabdruck** des Host-Schlüssels.

Danach in der Firewall **TCP 22222** von außen auf den Server freigeben bzw. weiterleiten.

## 5. Einrichtung abschließen
Zurück in der Einrichtung **Neu prüfen**. Beim Punkt **Sprung-Host** den angezeigten Fingerabdruck mit der Ausgabe des Installers vergleichen und **Fingerabdruck bestätigen**. Danach muss **Anmeldung am Sprung-Host: ok** erscheinen. Ein Punkt **Schreibrechte des API-Keys** mit Hinweis ist kein Fehler, er sagt nur, welche Knöpfe ohne die Rechte nicht gehen.

## 6. Erste Verbindung
**Zu den Sites**, Haken bei **auch Sites ohne Ziele**, bei der gewünschten Site **Bearbeiten**:
- unter **Websites** Name und Adresse eintragen, z. B. `Firewall` und `192.168.1.1:443`. `host:port` reicht, HTTP oder HTTPS erkennt der Client selbst.
- optional unter **Tunnel-Agenten** den Agenten wählen, der den Tunnel aufbauen soll.

**In TRMM speichern**, dann **Verbinden**. Nach 10 bis 30 Sekunden erscheinen die Ziele als Links. Ein Klick öffnet sie im eigenen Browserprofil. **Beenden** schließt den Tunnel. Ohne Klick endet er nach 30 Minuten ohne Verkehr, spätestens nach 4 Stunden.

Klappt etwas nicht: [Diagnose](../07-fehlerbehebung/01-diagnose.md).

## Weiter
- [Weitere Techniker](../03-installation/06-weitere-techniker.md) einrichten
- [Sicherheitsmodell](../02-konzept/03-sicherheitsmodell.md) lesen, bevor der erste Kunde dazukommt
- [Updates](../05-betrieb/01-updates.md) und [Logs](../05-betrieb/02-logs.md)
