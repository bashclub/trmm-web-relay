---
title: Die Steuerseite
audience: Anwender
outline:
outline_id:
---
## Starten
Doppelklick auf **TRMM Web-Relay** (Desktop, Startmenü bzw. Programme). Der Client startet im Hintergrund und öffnet die Steuerseite `http://127.0.0.1:8765/` in einem eigenen Browserfenster. Läuft er schon, öffnet der Doppelklick nur die Seite. Auf der Kommandozeile geht dasselbe mit `trmm-web-relay`.

Das Fenster gehört zum eigenen Browserprofil von Web-Relay, nicht zum normalen Browser. Lesezeichen, Erweiterungen und Anmeldungen aus dem normalen Profil gibt es dort nicht; das ist gewollt.

## Aufbau
Oben in der Leiste:
- **Servername** bzw. Auswahl des TRMM-Servers, wenn mehrere eingerichtet sind ([Mehrere TRMM-Server](04-mehrere-server.md))
- **Kunde oder Site suchen**: filtert die Liste beim Tippen
- **auch Sites ohne Ziele**: zeigt alle Sites, auch die ohne eingetragene Websites, z. B. um welche anzulegen
- **Neu laden**: liest Sites, Ziele und Felder neu aus TRMM. Der Client lädt beim Start und nach dem Speichern, Änderungen direkt in TRMM sieht er erst nach **Neu laden**.
- **Einrichtung**: Server anlegen und prüfen ([Einrichtung im Client](../03-installation/04-einrichtung.md))
- **Beenden**: beendet alle Sitzungen und den Client

Darunter die Sites, gruppiert nach Kunde. Jede Site zeigt ihren Namen, den Status bzw. den bevorzugten Tunnel-Agenten, die Knöpfe **Bearbeiten** und **Verbinden** und ihre Ziele.

Steht oben ein roter Hinweis, konnte der Client TRMM nicht lesen (Key, Rechte, Netz). Die Meldung nennt den Grund; die Einrichtung zeigt Einzelheiten.

## Beenden
**Beenden** oben rechts fragt nach, beendet alle Tunnel (inklusive Stopp-Skript auf den Agenten) und schließt den Client. Das Browserfenster kann danach zu. Wer nur das Fenster schließt, beendet den Client nicht; offene Sitzungen laufen weiter, bis Leerlauf oder Höchstdauer sie beenden. Ein neuer Doppelklick öffnet die Seite wieder.

Unter Linux und macOS beendet auch `Strg+C` im Terminal bzw. ein `SIGTERM` den Client sauber.
