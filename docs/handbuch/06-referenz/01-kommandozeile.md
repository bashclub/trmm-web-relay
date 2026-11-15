---
title: Kommandozeile
audience: Admin
outline: https://docs.bashclub.org/doc/kommandozeile-rS7PNKljIe
outline_id: 37d716bf-8069-4a20-8616-a8f7a7f78f88
---
```
trmm-web-relay [-v] [Befehl]
```
Ohne Befehl wie `serve`: Client starten bzw. die Steuerseite öffnen, wenn er schon läuft. Das Startsymbol ruft genau das auf. `-v` (`--verbose`) schreibt ausführlicher ins Log. `--version` zeigt die installierte Version.

Alle Befehle enden mit Status 0 bei Erfolg und 1 bei einem Fehler.

## `serve`
Startet den Client: Steuerseite auf `127.0.0.1:<control_port>`, SOCKS-Verteiler auf `127.0.0.1:<socks_port>`, und öffnet die Steuerseite im eigenen Browserprofil (ohne eingerichteten Server die Einrichtung). Läuft schon ein Client auf dem Port, öffnet er nur die Seite und endet. Zeigt ein Symbol im Infobereich, wenn es einen gibt ([Die Steuerseite](../04-bedienung/01-steuerseite.md#symbol-im-infobereich)). Protokoll in `~/.local/share/trmm-web-relay/client.log`, im Terminal zusätzlich auf dem Bildschirm. `Strg+C` bzw. `SIGTERM` beendet alle Sitzungen und den Client.

| Option | Bedeutung |
|---|---|
| `--no-browser` | Steuerseite nicht öffnen |

## `check`
Prüft die Einrichtung aller Server wie **Prüfen** in der Einrichtung, nur lesend, ob ein Browser gefunden wird und ob es eine neuere Version gibt (`update_url`; nur ein Hinweis, kein Fehler). Je Punkt eine Zeile mit `ok`, `info`, `FEHLT` oder `FEHLER`. Status 1, wenn etwas fehlt.
```
Konfiguration: /home/anna/.config/trmm-web-relay/config.toml
== Mein MSP
ok    TRMM https://api.example.com
info  Schreibrechte des API-Keys: Fehlt: Manage Scripts, Manage Custom Fields. Nur nötig für: …
ok    Feld „Tunnel-Ziele“ an Sites
…
ok    Anmeldung am Sprung-Host
ok    Browser: /usr/bin/brave-browser
ok    Version 0.6.0
```

## `ssh`
```
trmm-web-relay ssh [--wait] ZIEL [BEFEHL …]
```
Ab 0.6. Öffnet `ssh` zu einem Gerät im Kundennetz über den Tunnel einer offenen Sitzung; der Client muss laufen und die Site verbunden sein. `ZIEL` ist `[benutzer@]host` oder `ssh://[benutzer@]host[:port]`, `BEFEHL` läuft wie bei `ssh` auf dem Gerät. Es ist das normale `ssh` mit eigenen Schlüsseln, `ssh-agent` und `~/.ssh/config`, dazu:
- als `ProxyCommand` `trmm-web-relay proxy %h %p`,
- die Host-Schlüssel je Site in `~/.local/share/trmm-web-relay/known_hosts.d/`,
- `ServerAliveInterval=60`, damit ein offenes Terminal die Sitzung aktiv hält.

Ohne Sitzung zum Host endet der Befehl mit `Keine offene Sitzung erreicht …`. Der Klick auf ein SSH-Ziel der Steuerseite ruft ihn im Terminal auf.

| Option | Bedeutung |
|---|---|
| `--wait` | nach einem Fehler auf Enter warten, damit das Terminalfenster die Meldung zeigt |

## `proxy`
```
trmm-web-relay proxy HOST PORT
```
Ab 0.6. Verbindet Standardein- und -ausgabe mit `HOST:PORT` über den SOCKS-Verteiler, als `ProxyCommand` für eigene Aufrufe von `ssh`, `scp`, `sftp` oder Ansible. Der Host muss in einer offenen Sitzung liegen. Beispiel in `~/.ssh/config`:
```
Host 192.168.1.*
    ProxyCommand trmm-web-relay proxy %h %p
```
Gilt dann für alle Sitzungen; die Host-Schlüssel stehen dabei in `~/.ssh/known_hosts`, mit den Warnungen bei gleichen Adressen verschiedener Kunden.

## `stop`
Beendet den laufenden Client wie **Beenden** auf der Steuerseite: alle Sitzungen (inklusive Stopp-Skript auf den Agenten), dann den Client. Der Befehl wartet nicht, bis alle Stopp-Skripte gelaufen sind. Läuft kein Client, meldet er `Client läuft nicht` und endet mit Status 0. Unter Linux ruft der Eintrag **Beenden** im Kontextmenü des Startsymbols diesen Befehl auf.

## `targets`
Zeigt je Server die Sites mit Zielen, den Agenten, den der Client wählen würde, und wie er die Ziele versteht. Fehler im Feld **Tunnel-Ziele** stehen mit `!` darunter. Nur lesend.

| Option | Bedeutung |
|---|---|
| `--all` | auch Sites ohne Ziele |

## `desktop`
Legt das Startsymbol **TRMM Web-Relay** auf dem Desktop und im Startmenü an (Linux: `.desktop`-Datei, als vertrauenswürdig markiert, mit der Aktion **Beenden**; macOS: `~/Applications/TRMM Web-Relay.app` und Verknüpfung auf dem Schreibtisch; Windows: Verknüpfungen ohne Konsolenfenster). Der Installer ruft das auf.

| Option | Bedeutung |
|---|---|
| `--remove` | Startsymbol entfernen |
