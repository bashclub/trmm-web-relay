---
title: Erweiterungen und Passwortmanager
audience: Anwender, Admin
outline: https://docs.bashclub.org/doc/erweiterungen-und-passwortmanager-QbzLg79Lo9
outline_id: 315ad1b9-fbb4-48a8-8350-117d09eb5b8b
---
Ab 0.3 lassen sich im Web-Relay-Profil Browser-Erweiterungen nutzen, vor allem ein Passwortmanager wie Bitwarden. So kommen alle Techniker mit Zugriff auf den gemeinsamen Tresor an die Zugangsdaten der Geräte, nicht nur der, der sie im Browser gespeichert hat.

## Was das Profil erreicht
Das Profil kommt nicht frei ins Internet. Der Verteiler des Clients lässt durch:
- die Ziele und Netze offener Sitzungen, durch den Tunnel,
- den Chrome Web Store und die Server für Download und Updates von Erweiterungen (`extension_store`, Standard an),
- die Hosts in `direct_hosts`, direkt ohne Tunnel, nur Port 443, wenn kein anderer angegeben ist.

Alles andere lehnt er ab. Erweiterungen, die nur im Browser arbeiten, laufen also ohne weiteres; brauchen sie einen Server, gehört er in `direct_hosts`. Welche Hosts abgelehnt wurden, steht im Log (`~/.local/share/trmm-web-relay/client.log`), je Host einmal:
```
2026-11-08 15:02:11,204 INFO trmmwebrelay.socks: abgelehnt (kein Ziel einer Sitzung, nicht in direct_hosts): api.example.com:443
```

## Bitwarden einrichten
1. Server freigeben. In `~/.config/trmm-web-relay/config.toml` oben (vor dem ersten `[[server]]`) eintragen, je nach Bitwarden-Server:
   ```toml
   # Bitwarden Cloud, Region EU
   direct_hosts = ["bitwarden.eu"]
   # Bitwarden Cloud, Region US (Symbole von bitwarden.net)
   # direct_hosts = ["bitwarden.com", "bitwarden.net"]
   # eigener Server (Vaultwarden oder Bitwarden selbst gehostet)
   # direct_hosts = ["vault.example.com"]
   ```
   Ein Eintrag gilt mit allen Subdomains, `bitwarden.eu` also auch für `vault.bitwarden.eu`, `api.bitwarden.eu` und `identity.bitwarden.eu`.
2. Client beenden (**Beenden** oben auf der Steuerseite) und alle Fenster des Web-Relay-Profils schließen, dann neu starten.
3. Im Profil die Erweiterung installieren: in der Adresszeile `chromewebstore.google.com` öffnen, nach „Bitwarden“ suchen, **Hinzufügen**. Das Symbol über das Puzzle-Symbol neben der Adresszeile anheften.
4. In der Erweiterung beim Anmelden den Server wählen (bitwarden.com, bitwarden.eu oder **Selbst gehostet** mit eigener Adresse), anmelden.

Erweiterung, Server und Anmeldung bleiben im Profil gespeichert (`~/.local/share/trmm-web-relay/browser`), auch beim Beenden des Clients und bei Updates. Nach einem Neustart des Browsers fragt Bitwarden nur nach dem Master-Passwort bzw. der PIN, so wie eingestellt.

## Tipps für Zugangsdaten
- Gemeinsame Zugangsdaten in eine Organisation bzw. Sammlung legen, auf die alle Techniker Zugriff haben.
- Viele Kunden nutzen dieselben Adressen (`192.168.1.1`). Bitwarden schlägt dann die Einträge aller Kunden vor. Deshalb den Kunden in den Namen des Eintrags schreiben, z. B. „Musterkunde Firewall“, oder je Kunde eine eigene Sammlung anlegen.
- Als URI die Adresse eintragen, die im Profil in der Adresszeile steht, mit Port, z. B. `https://192.168.1.1:8443`.

## Zertifikate
Damit die Verbindung zum Passwortmanager sicher ist, prüft das Profil ab 0.3 Zertifikate wie ein normaler Browser. Selbstsignierte Zertifikate der Geräte zeigen deshalb eine Warnung: **Erweitert → Weiter zu … (unsicher)**. Mit `ignore_cert_errors = true` verschwinden die Warnungen, aber dann auch für den Passwortmanager. Das passt nicht zu `direct_hosts`. Siehe [Konfiguration](../06-referenz/02-konfiguration.md#ignore_cert_errors).

## Andere Erweiterungen
Jede Erweiterung läuft mit den Rechten des Profils und sieht die Seiten der Kundengeräte. Nur Erweiterungen installieren, denen man auch die Zugangsdaten der Kunden anvertrauen würde, und `direct_hosts` kurz halten.
