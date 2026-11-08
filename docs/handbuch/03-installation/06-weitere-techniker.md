---
title: Weitere Techniker
audience: Admin
outline:
outline_id:
---
Jeder Techniker hat einen eigenen Client mit eigener CA und eigenem TRMM-Key. Felder und Skripte in TRMM gibt es nur einmal je TRMM-Server, der Sprung-Host bleibt derselbe.

## Ablauf
1. **TRMM**: Benutzer für den neuen Techniker mit der Rolle `web-relay` anlegen und einen API-Key für diesen Benutzer erzeugen ([TRMM vorbereiten](02-trmm-vorbereiten.md#benutzer-und-key-je-techniker)). Die Schreibrechte braucht er meist nicht.
2. **Client** installieren ([Client installieren](03-client.md)) und in der Einrichtung den Server mit **denselben** Werten für TRMM-API-Adresse und Sprung-Host anlegen, aber mit seinem eigenen Key.
3. **CA erzeugen** und den **Installer herunterladen**.
4. Den Installer auf dem Sprung-Host ausführen. Er erkennt die vorhandene Installation, behält alle Einstellungen und fügt die neue CA zu `TRUSTED_CA` hinzu; nach dem Lese-Key fragt er nicht noch einmal.
5. Im Client **Neu prüfen**, Fingerabdruck bestätigen (es ist derselbe wie beim ersten Techniker), Anmeldung ok.

Statt den Installer auszuführen, kann der Admin des Sprung-Hosts die CA-Zeile des Technikers auch selbst in `TRUSTED_CA` eintragen (Datei `/etc/trmm-web-relay/jumphost.env`, Einträge mit `;` getrennt) und den Dienst neu starten:
```bash
systemctl restart trmm-web-relay-jumphost.service
```

## Mehrere Rechner eines Technikers
Jeder Rechner hat seine eigene CA. Ein Techniker mit Laptop und Arbeitsplatz richtet beide ein; beide CAs stehen in `TRUSTED_CA`. Den API-Key kann er auf beiden verwenden oder je Rechner einen eigenen anlegen.

## Wer welche CA ist
Die Kommentare der CA-Zeilen nennen Server, Benutzer und Rechner, z. B. `trmm-web-relay-ca msp anna@laptop`. Das Log des Sprung-Hosts zeigt beim Start je CA den Fingerabdruck; die Einrichtung im Client zeigt den Fingerabdruck der eigenen CA. Einen Techniker sperren: [Zugang entziehen](../05-betrieb/04-zugang-entziehen.md).
