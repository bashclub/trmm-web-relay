---
title: Verbinden und arbeiten
audience: Anwender
outline: https://docs.bashclub.org/doc/verbinden-und-arbeiten-6PvMYwuw9A
outline_id: 6513d6b1-61f8-4d03-98fc-9c0687293655
---
## Verbinden
**Verbinden** bei einer Site. Der Knopf ist grau, solange die Site keine Ziele hat; dann zuerst [Sites bearbeiten](03-sites-bearbeiten.md). Der Status zeigt die Schritte:
1. **startet · Agent wählen**
2. **startet über `<agent>` · Tunnel auf `<agent>` starten**: TRMM führt das Start-Skript aus
3. **Mit dem Sprung-Host verbinden**, **Warten auf den Tunnel von `<agent>`**: bis zu 90 Sekunden
4. **Ziele erkennen**: HTTP oder HTTPS, Seitentitel
5. **verbunden über `<agent>` · Leerlauf noch 30 min, höchstens 4 h**

Meist dauert das 10 bis 30 Sekunden, je nachdem, wie schnell der Agent den Auftrag von TRMM abholt. Unter dem Status stehen die **Netze im Tunnel** und, falls der bevorzugte Agent nicht ging, ein **Hinweis**, z. B. `nas01: offline; Ausweichen auf pve01`.

## Arbeiten
Die Ziele werden zu Links. Ein Klick öffnet die Seite in einem neuen Tab des Web-Relay-Profils. Ohne eingetragenen Namen zeigt der Link den Seitentitel. Ein Ziel, das nicht antwortet, ist rot markiert, mit dem Grund darunter.

Im Tunnel erreichbar sind nicht nur die eingetragenen Ziele, sondern alle Adressen in den **Netzen im Tunnel**: die privaten IPv4-Netze des Agenten (ab /16). Ein Link von der Firewall auf den Switch im selben Netz funktioniert also, und eine Adresse kann man auch von Hand in die Adresszeile des Profils tippen. Hostnamen gehen nur, wenn sie als Ziel eingetragen sind.

Mehrere Sitzungen zu verschiedenen Sites können gleichzeitig offen sein, auch wenn die Kunden dieselben Adressbereiche nutzen. Dann geht eine Adresse an die neuere Sitzung. Wer zwischen zwei Kunden mit gleichem Netz wechselt, beendet am besten die alte Sitzung.

Selbstsignierte Zertifikate der Geräte zeigen die übliche Warnung des Browsers: **Erweitert → Weiter zu … (unsicher)**. Der Browser merkt sich die Ausnahme je Adresse, bis er geschlossen wird. Ins Internet kommt das Profil nur zu wenigen freigegebenen Hosts, etwa für einen Passwortmanager, siehe [Erweiterungen und Passwortmanager](05-erweiterungen.md). Das Profil liegt in `~/.local/share/trmm-web-relay/browser` und bleibt beim Beenden und bei Updates erhalten.

:::info
**Geändert in 0.3:** Bis 0.2 hat das Profil Zertifikatsfehler ignoriert und keine Warnung gezeigt. Ab 0.3 prüft es Zertifikate wie ein normaler Browser, damit Erweiterungen wie ein Passwortmanager sicher ins Internet dürfen. Wer das alte Verhalten braucht, setzt `ignore_cert_errors = true` ([Konfiguration](../06-referenz/02-konfiguration.md#ignore_cert_errors)). Läuft das Profil beim Update noch, gilt die Änderung erst, wenn alle seine Fenster geschlossen waren.
:::

## Beenden
- **Beenden** bei der Site beendet diese Sitzung.
- Nach **30 Minuten ohne Verkehr** endet sie von selbst, spätestens nach **4 Stunden**. Die Restzeit steht im Status. Jede Verbindung durch den Tunnel, auch das Nachladen einer offenen Seite, setzt den Leerlauf zurück.
- Bricht eine Verbindung ab, steht die Sitzung auf **Fehler** mit dem Grund.

Danach lässt sich die Site sofort wieder verbinden. Leerlauf und Höchstdauer sind einstellbar ([Konfiguration](../06-referenz/02-konfiguration.md)).
