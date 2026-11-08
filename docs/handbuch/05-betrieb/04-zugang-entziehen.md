---
title: Zugang entziehen
audience: Admin
outline: https://docs.bashclub.org/doc/zugang-entziehen-S1M4uDsk7p
outline_id: c2fe3a22-19fa-46e4-b58b-9f29f9d1f60b
---
## Techniker sperren
Ein Techniker braucht für einen Tunnel zwei Dinge: einen TRMM-Key mit `Run Scripts` und eine CA, die der Sprung-Host kennt. Es reicht, eines davon zu entziehen; sauber ist beides.

1. **TRMM**: den API-Key des Technikers löschen (Settings → Global Settings → API Keys) und seinen Benutzer deaktivieren. Ab sofort kann er keine Tunnel mehr starten und keine Ziele mehr lesen.
2. **Sprung-Host**: seine CA-Zeile(n) aus `TRUSTED_CA` entfernen und den Dienst neu starten. Die Zeile erkennt man am Kommentar (`trmm-web-relay-ca <server> <benutzer>@<rechner>`).
   ```bash
   nano /etc/trmm-web-relay/jumphost.env
   systemctl restart trmm-web-relay-jumphost.service
   podman logs trmm-web-relay-jumphost | grep 'Vertraute CA'
   ```
   Rootless liegt die Datei unter `~/.config/trmm-web-relay/jumphost.env`, der Dienst heißt gleich (`systemctl --user`).

Der Container liest `TRUSTED_CA` nur beim Start; ohne Neustart gilt die alte Liste weiter. Der Neustart trennt alle offenen Tunnel, sie lassen sich danach sofort neu verbinden.

## Rechner verloren
Ein verlorener Laptop hat API-Key und CA im Schlüsselbund. Beides wie oben entziehen. Der Schlüsselbund ist mit dem Benutzerkonto verschlüsselt; ohne Schlüsselbund (Dateien in `~/.local/share/trmm-web-relay/secrets/`) schützt nur die Plattenverschlüsselung.

## API-Key tauschen
Neuen Key in TRMM erzeugen, in der Einrichtung **Bearbeiten** beim Server und den neuen Key eintragen, alten Key in TRMM löschen. Die CA bleibt.

## CA tauschen
Eine CA lässt sich nicht einzeln neu erzeugen, solange der Server eingerichtet ist. Weg:
1. Alte CA-Zeile aus `TRUSTED_CA` entfernen.
2. In der Einrichtung den Server **Entfernen** (löscht Key und CA) und neu anlegen, **CA erzeugen**.
3. Neue CA mit dem Installer oder von Hand in `TRUSTED_CA` eintragen.

## Sprung-Host neu aufsetzen
Ohne das alte Volume entsteht ein neuer Host-Schlüssel. Jeder Client meldet dann bei **Prüfen**, dass sich der Host-Schlüssel geändert hat, und baut keine Tunnel, bis jemand den neuen Fingerabdruck bestätigt. Das ist gewollt; mit gesichertem Volume bleibt der Schlüssel gleich ([Sicherung](05-sicherung.md)).
