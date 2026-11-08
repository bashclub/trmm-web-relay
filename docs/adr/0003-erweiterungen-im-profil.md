# ADR 0003: Erweiterungen im Browserprofil

Status: angenommen (2026-11-08), ändert ADR 0001 (Eigenes Browserprofil)

## Kontext

Bis 0.2 kam das Browserprofil nur zu den Zielen aktiver Sitzungen und lief mit `--ignore-certificate-errors`. Erweiterungen ließen sich darin weder installieren noch nutzen, wenn sie einen Server brauchen. Techniker brauchen im Profil aber einen gemeinsamen Passwortmanager (z. B. Bitwarden), damit nicht nur einer die Zugangsdaten der Geräte kennt.

Das Profil einfach ins Internet zu lassen, geht nicht:
- Mit ignorierten Zertifikatsfehlern könnte sich jeder im Netz des Technikers als Server des Passwortmanagers ausgeben.
- Jede Webseite im Profil könnte im Hintergrund Anfragen an Geräte in offenen Tunneln schicken (z. B. an `192.168.1.1`).

## Entscheidung

- Das Profil prüft Zertifikate wie ein normaler Browser. Selbstsignierte Zertifikate der Geräte zeigen die übliche Warnung, durch die der Techniker sich klickt. `ignore_cert_errors = true` stellt das alte Verhalten her.
- Der Verteiler lässt zusätzlich zu den Sitzungen einzelne Hosts direkt ins Internet:
  - den Chrome Web Store und die Download- und Update-Server für Erweiterungen (`extension_store`, Standard an; feste Liste im Code, Chrome, Brave, Edge),
  - die Hosts in `direct_hosts`, mit Subdomains, nur Port 443, außer der Eintrag nennt einen Port.
- Sitzungen haben Vorrang vor `direct_hosts`. Direkte Verbindungen zählen nicht als Aktivität einer Sitzung.
- Abgelehnte Hosts stehen je einmal im Log, damit sich `direct_hosts` pflegen lässt.

Kein Passwortmanager ist voreingestellt, weil das Werkzeug allgemein für MSPs ist.

## Folgen

- Passwortmanager und andere Erweiterungen funktionieren im Profil; ihre Einstellungen bleiben im Profilordner.
- Mehr Klicks bei Geräten mit selbstsignierten Zertifikaten (eine Warnung je Adresse und Browserstart).
- Die Angriffsfläche wächst um die freigegebenen Hosts und die installierten Erweiterungen. Das Handbuch rät, `direct_hosts` kurz zu halten und nur vertrauenswürdige Erweiterungen zu installieren.
