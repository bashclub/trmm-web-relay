---
title: Was ist TRMM Web-Relay
audience: Anwender, Admin
outline: https://docs.bashclub.org/doc/was-ist-trmm-web-relay-ZBNQVIEaZE
outline_id: 06395e3b-0e11-41dd-9abe-a56e5a5c7b21
---
TRMM Web-Relay öffnet Weboberflächen in Kundennetzen, ohne dass dafür ein Tunnel dauerhaft offen ist. Tactical RMM (TRMM) bringt Shell, Dateien und Fernsteuerung schon mit, aber keinen Weg zu den Weboberflächen von Firewall, Hypervisor, NAS, Switch oder Drucker. Diese Geräte haben oft keinen Agenten. Web-Relay schließt diese Lücke über einen Agenten, der in der Site ohnehin läuft.

## Bestandteile
- **Client** auf dem Rechner des Technikers: eine lokale Steuerseite (`http://127.0.0.1:8765`), ein SOCKS-Verteiler (`127.0.0.1:8766`) und ein eigenes Browserprofil. Er spricht mit der TRMM-API und per SSH mit dem Sprung-Host. Linux, macOS und Windows.
- **Sprung-Host**: ein Container mit nur `sshd`, betrieben vom MSP, je TRMM-Server einer. Agenten und Clients treffen sich dort. Er lässt nur Weiterleitungen auf `127.0.0.1` zu, keine Shell.
- **Zwei TRMM-Skripte**: **Web-Relay: Tunnel starten** und **Web-Relay: Tunnel stoppen**. Der Client legt sie bei der Einrichtung in TRMM an und startet sie je Sitzung auf einem Agenten.
- **Zwei Benutzerfelder an der Site** in TRMM: **Tunnel-Ziele** (die Websites) und **Tunnel-Agent** (welche Agenten den Tunnel bauen sollen). Es gibt kein zweites Inventar.

## Was Web-Relay tut
- Es startet auf Klick einen Reverse-SOCKS-Tunnel von einem Agenten der Site zum Sprung-Host.
- Es öffnet die Ziele unter ihrer echten Adresse (`https://192.168.1.1`) in einem eigenen Browserprofil. Weiterleitungen, Websockets und Links auf andere Geräte im selben Netz funktionieren.
- Es beendet den Tunnel auf Klick, nach 30 Minuten ohne Verkehr oder spätestens nach 4 Stunden.
- Es meldet sich bei jedem Schritt mit kurzlebigen Zertifikaten an, die nur für diese Sitzung gelten.

## Was es nicht tut
- **Nur TCP, nur im Browser.** RDP, SMB, SSH aus anderen Programmen, UDP oder Ping gehen nicht durch den Tunnel. Für Shell und Desktop hat TRMM eigene Wege.
- **Agenten unter Linux und macOS.** Windows-Agenten können den Tunnel noch nicht bauen. In einer Site mit nur Windows-Geräten braucht es einen Linux-Rechner, z. B. eine kleine VM, den Hypervisor oder einen Raspberry Pi mit TRMM-Agent.
- **Kein Ersatz für TRMM-Rechte.** Wer im TRMM des MSP Skripte auf einer Site ausführen darf, kann auch tunneln. Web-Relay schränkt das nicht weiter ein.

## Voraussetzungen im Überblick
| Teil | braucht |
|---|---|
| TRMM | API erreichbar für Client und Sprung-Host, Benutzer mit passender Rolle und API-Key ([TRMM-Rechte](../06-referenz/06-trmm-rechte.md)) |
| Agent | Linux oder macOS, `bash`, `ssh`, `base64`, `pkill`; ausgehend TCP über IPv4 zum Sprung-Host |
| Sprung-Host | Linux mit Podman ab 4.4 und systemd, ein TCP-Port von außen (Vorschlag 22222), nur IPv4 |
| Client | OpenSSH-Client, Brave, Chromium, Chrome oder Edge; Python ab 3.11 bringt der Installer über `uv` mit |
