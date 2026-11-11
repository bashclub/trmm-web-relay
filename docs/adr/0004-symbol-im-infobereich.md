# ADR 0004: Symbol im Infobereich

Status: angenommen (2026-11-11)

## Kontext

Der Client läuft ohne Terminal im Hintergrund. Bis 0.4 ließ er sich nur über **Beenden** auf der Steuerseite, `Strg+C` oder `SIGTERM` beenden. War das Fenster zu, sah man nicht, dass er noch lief und vielleicht Tunnel offen hatte.

Übliche Bibliotheken für ein Tray-Symbol passen nicht gut:
- pystray braucht unter Linux für StatusNotifier PyGObject mit der AppIndicator-Bibliothek des Systems. Das lässt sich mit `uv tool install` (eigenes Python, eigene Umgebung) nicht verlässlich installieren; der Rückfall über X11 (XEmbed) erscheint unter Wayland und GNOME nicht.
- Qt oder GTK als Abhängigkeit wären für ein Menü mit fünf Einträgen zu groß.

## Entscheidung

- Linux: Der Client meldet sich selbst als StatusNotifierItem mit DBusMenu am D-Bus an (`tray_sni.py`). Dafür reicht jeepney, das über `keyring` (SecretStorage) ohnehin installiert ist; es steht jetzt ausdrücklich in den Abhängigkeiten.
- Windows und macOS: pystray mit Pillow (nur auf diesen Plattformen installiert). Unter macOS läuft das Symbol im Haupt-Thread, das verlangt das System.
- Menü für alle gleich (`tray.py`): Steuerseite öffnen, Einrichtung, Zahl der offenen Sitzungen, Alle Sitzungen beenden, Beenden. Statt einer Nachfrage nennt **Beenden** die Zahl der Sitzungen, die es schließt; ein Tray-Menü kann keine Rückfrage zeigen.
- Ohne Infobereich (GNOME ohne AppIndicator, kein D-Bus, Bibliothek fehlt) läuft der Client ohne Symbol weiter und schreibt den Grund ins Log. Unter Linux meldet sich das Symbol an, sobald ein Infobereich erscheint.
- Unabhängig vom Symbol: Befehl `trmm-web-relay stop` und unter Linux die Aktion **Beenden** im Startsymbol.

## Folgen

- Unter GNOME braucht das Symbol die Erweiterung „AppIndicator and KStatusNotifierItem Support“ (Ubuntu hat sie vorinstalliert). Das Handbuch nennt sie.
- Unter Windows und macOS zwei Pakete mehr (pystray, Pillow). Beides ist dort noch nicht ausprobiert.
- Das StatusNotifier-Protokoll pflegt der Client selbst (rund 250 Zeilen); Änderungen an GNOME-Erweiterung oder KDE können Nacharbeit verlangen.
