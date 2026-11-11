---
title: Die Steuerseite
audience: Anwender
outline: https://docs.bashclub.org/doc/die-steuerseite-Tq2ovph72U
outline_id: 26ec2124-5bf5-4267-8858-fdc6a9887206
---
## Starten
Doppelklick auf **TRMM Web-Relay** (Desktop, Startmenü bzw. Programme). Der Client startet im Hintergrund und öffnet die Steuerseite `http://127.0.0.1:8765/` in einem eigenen Browserfenster. Läuft er schon, öffnet der Doppelklick nur die Seite. Auf der Kommandozeile geht dasselbe mit `trmm-web-relay`.

Das Fenster gehört zum eigenen Browserprofil von Web-Relay, nicht zum normalen Browser. Lesezeichen, Erweiterungen und Anmeldungen aus dem normalen Profil gibt es dort nicht; das ist gewollt. Einen Passwortmanager richtet man im Profil eigens ein ([Erweiterungen und Passwortmanager](05-erweiterungen.md)).

## Aufbau
Oben in der Leiste:
- **Servername** bzw. Auswahl des TRMM-Servers, wenn mehrere eingerichtet sind ([Mehrere TRMM-Server](04-mehrere-server.md))
- **Kunde oder Site suchen**: filtert die Liste beim Tippen
- **auch Sites ohne Ziele**: zeigt alle Sites, auch die ohne eingetragene Websites, z. B. um welche anzulegen
- **Neu laden**: liest Sites, Ziele und Felder neu aus TRMM. Der Client lädt beim Start und nach dem Speichern, Änderungen direkt in TRMM sieht er erst nach **Neu laden**.
- **Einrichtung**: Server anlegen und prüfen ([Einrichtung im Client](../03-installation/04-einrichtung.md))
- **Beenden**: beendet alle Sitzungen und den Client

Darunter die Sites, gruppiert nach Kunde. Jede Site zeigt ihren Namen, den Status bzw. den bevorzugten Tunnel-Agenten, die Knöpfe **Bearbeiten** und **Verbinden** und ihre Ziele.

Neben dem Namen steht die installierte Version. Gibt es eine neuere, steht oben ein blauer Hinweis mit den Befehlen zum Aktualisieren ([Updates](../05-betrieb/01-updates.md)).

Steht oben ein roter Hinweis, konnte der Client TRMM nicht lesen (Key, Rechte, Netz). Die Meldung nennt den Grund; die Einrichtung zeigt Einzelheiten.

## Symbol im Infobereich
Ab 0.5 zeigt der Client ein Symbol im Infobereich (Tray, neben Uhr bzw. Netzwerk), solange er läuft, auch wenn das Fenster zu ist. Ein Klick darauf öffnet das Menü:
- **Steuerseite öffnen**
- **Einrichtung**
- die Zahl der offenen Sitzungen (nur Anzeige, auch als Tooltip)
- **Alle Sitzungen beenden**: beendet die Tunnel, der Client läuft weiter
- **Beenden**: beendet alle Sitzungen und den Client. Sind Sitzungen offen, steht ihre Zahl im Eintrag, z. B. „Beenden (2 Sitzungen schließen)“; eine weitere Nachfrage gibt es nicht.

Unter **GNOME** (z. B. Fedora, Debian) erscheint das Symbol nur mit der Erweiterung „AppIndicator and KStatusNotifierItem Support“; Ubuntu bringt sie mit. KDE Plasma, Cinnamon, XFCE, MATE, Budgie, LXQt, Windows und macOS zeigen es ohne Zusatz. Fehlt der Infobereich, läuft der Client ohne Symbol, beenden lässt er sich dann auf den anderen Wegen unten. Siehe [Voraussetzungen](../03-installation/01-voraussetzungen.md#rechner-des-technikers).

## Beenden
Den Client beenden, wahlweise:
- **Beenden** im Menü des Symbols im Infobereich
- **Beenden** oben rechts auf der Steuerseite (fragt nach)
- Linux: Rechtsklick auf **TRMM Web-Relay** im Startmenü bzw. Dock → **Beenden**
- Kommandozeile: `trmm-web-relay stop`; im Terminal, in dem der Client läuft, auch `Strg+C`

Jeder Weg beendet alle Tunnel (inklusive Stopp-Skript auf den Agenten) und schließt den Client. Das Browserfenster kann danach zu. Wer nur das Fenster schließt, beendet den Client nicht; offene Sitzungen laufen weiter, bis Leerlauf oder Höchstdauer sie beenden. Ein neuer Doppelklick öffnet die Seite wieder.
