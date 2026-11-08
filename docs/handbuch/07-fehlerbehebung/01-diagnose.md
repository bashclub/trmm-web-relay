---
title: Diagnose
audience: Admin
outline: https://docs.bashclub.org/doc/diagnose-lVm6ET0zGU
outline_id: 4d8d717c-1ee9-46ea-b6d1-ad6d18852742
---
Ein Tunnel hat drei Abschnitte: Client → TRMM, Agent → Sprung-Host, Client → Sprung-Host. Die Meldung auf der Steuerseite sagt meist schon, welcher es ist. Sonst in dieser Reihenfolge prüfen.

## 1. Einrichtung
```bash
trmm-web-relay check
```
Alles muss `ok` oder `info` sein. Ein `FEHLT` oder `FEHLER` nennt den Grund ([Einrichtung im Client](../03-installation/04-einrichtung.md)). `Anmeldung am Sprung-Host: ok` heißt: Client, CA, Host-Schlüssel und `ADMIN_FROM` passen.

## 2. Ziele und Agent
```bash
trmm-web-relay targets
```
zeigt je Site, welchen Agenten der Client nehmen würde und warum er andere übersprungen hat, und ob er die Ziele versteht.

## 3. Lauf des Start-Skripts in TRMM
Agent → **History**: Lief **Web-Relay: Tunnel starten**? Die Ausgabe erscheint erst, wenn das Skript endet. Läuft der Tunnel, gibt es noch keine Ausgabe; ist er sofort gescheitert, steht dort die Meldung von `ssh`, z. B. `Permission denied` oder `Connection timed out`.

Zum Testen ohne Client von Hand auf dem Agenten:
```bash
host=relay.example.com port=22222
nc -vz -w 5 "$host" "$port"
```
Antwortet der Port nicht, liegt es an Firewall, Portweiterleitung, DNS oder einer Sperrliste.

## 4. Log des Sprung-Hosts
```bash
journalctl -t sshd --since -15min
```
Kommt die Anmeldung des Agenten an? `not from a permitted host` heißt: Der Sprung-Host kennt die Absenderadresse noch nicht ([Typische Fehler](02-typische-fehler.md#permission-denied-beim-agenten)). Steht gar nichts da, erreicht der Agent den Sprung-Host nicht.

## 5. Client-Log
```bash
tail -n 50 ~/.local/share/trmm-web-relay/client.log
```
Fehler beim Start, beim Stopp-Skript und beim Verbinden mit dem Sprung-Host stehen hier. Für mehr Einzelheiten den Client mit `trmm-web-relay -v` im Terminal starten.
