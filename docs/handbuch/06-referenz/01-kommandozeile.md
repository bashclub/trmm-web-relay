---
title: Kommandozeile
audience: Admin
outline:
outline_id:
---
```
trmm-web-relay [-v] [Befehl]
```
Ohne Befehl wie `serve`: Client starten bzw. die Steuerseite öffnen, wenn er schon läuft. Das Startsymbol ruft genau das auf. `-v` (`--verbose`) schreibt ausführlicher ins Log.

Alle Befehle enden mit Status 0 bei Erfolg und 1 bei einem Fehler.

## `serve`
Startet den Client: Steuerseite auf `127.0.0.1:<control_port>`, SOCKS-Verteiler auf `127.0.0.1:<socks_port>`, und öffnet die Steuerseite im eigenen Browserprofil (ohne eingerichteten Server die Einrichtung). Läuft schon ein Client auf dem Port, öffnet er nur die Seite und endet. Protokoll in `~/.local/share/trmm-web-relay/client.log`, im Terminal zusätzlich auf dem Bildschirm. `Strg+C` bzw. `SIGTERM` beendet alle Sitzungen und den Client.

| Option | Bedeutung |
|---|---|
| `--no-browser` | Steuerseite nicht öffnen |

## `check`
Prüft die Einrichtung aller Server wie **Prüfen** in der Einrichtung, nur lesend, und ob ein Browser gefunden wird. Je Punkt eine Zeile mit `ok`, `info`, `FEHLT` oder `FEHLER`. Status 1, wenn etwas fehlt.
```
Konfiguration: /home/anna/.config/trmm-web-relay/config.toml
== Mein MSP
ok    TRMM https://api.example.com
info  Schreibrechte des API-Keys: Fehlt: Manage Scripts, Manage Custom Fields. Nur nötig für: …
ok    Feld „Tunnel-Ziele“ an Sites
…
ok    Anmeldung am Sprung-Host
ok    Browser: /usr/bin/brave-browser
```

## `targets`
Zeigt je Server die Sites mit Zielen, den Agenten, den der Client wählen würde, und wie er die Ziele versteht. Fehler im Feld **Tunnel-Ziele** stehen mit `!` darunter. Nur lesend.

| Option | Bedeutung |
|---|---|
| `--all` | auch Sites ohne Ziele |

## `desktop`
Legt das Startsymbol **TRMM Web-Relay** auf dem Desktop und im Startmenü an (Linux: `.desktop`-Datei, als vertrauenswürdig markiert; macOS: `~/Applications/TRMM Web-Relay.app` und Verknüpfung auf dem Schreibtisch; Windows: Verknüpfungen ohne Konsolenfenster). Der Installer ruft das auf.

| Option | Bedeutung |
|---|---|
| `--remove` | Startsymbol entfernen |
