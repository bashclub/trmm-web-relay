---
title: Häufige Fragen
audience: Anwender, Admin
outline: https://docs.bashclub.org/doc/haufige-fragen-2uDg8T8fHZ
outline_id: 925091c7-6277-4549-b568-a28e5bc938db
---
**Geht das auch mit Windows-Agenten?**
Noch nicht. Das Tunnel-Skript gibt es für Linux und macOS. Ein PowerShell-Skript für Windows ist geplant. Bis dahin hilft ein kleiner Linux-Rechner mit TRMM-Agent in der Site.

**Kann ich RDP, SSH oder SMB durch den Tunnel nutzen?**
Nein, nur Weboberflächen im eigenen Browserprofil. Für Shell und Desktop hat TRMM eigene Wege. Siehe [Vergleich mit VPN](../02-konzept/04-vergleich-mit-vpn.md).

**Muss beim Kunden ein Port offen sein?**
Nein. Der Agent baut die Verbindung nach außen zum Sprung-Host auf. Er braucht nur ausgehend TCP zum Port des Sprung-Hosts.

**Sehen andere Techniker meine Tunnel?**
Jeder Client sieht nur seine eigenen Sitzungen. In TRMM sieht jeder mit Zugriff auf den Verlauf des Agenten, dass ein Tunnel-Skript lief.

**Was passiert, wenn mein Laptop abstürzt?**
Der Tunnel endet spätestens nach der Höchstdauer (4 h): TRMM beendet das Skript. Der Sprung-Host trennt die Seite des Agenten etwa 45 Sekunden nachdem die Verbindung des Clients weg ist; dann endet `ssh` auf dem Agenten.

**Zwei Kunden haben dasselbe Netz. Geht das gleichzeitig?**
Ja. Eine Adresse geht an die neuere Sitzung. Um sicher beim richtigen Kunden zu landen, die alte Sitzung beenden.

**Wie beende ich den Client, wenn das Fenster zu ist?**
Über das Symbol im Infobereich → **Beenden**, unter Linux auch per Rechtsklick auf das Startsymbol → **Beenden**, oder mit `trmm-web-relay stop`. Ein Doppelklick auf das Startsymbol öffnet die Steuerseite wieder, dort steht **Beenden** oben rechts. Siehe [Die Steuerseite](../04-bedienung/01-steuerseite.md#beenden).

**Unter GNOME fehlt das Symbol im Infobereich.**
GNOME zeigt solche Symbole nur mit der Erweiterung „AppIndicator and KStatusNotifierItem Support“. Installieren und einschalten ([Voraussetzungen](../03-installation/01-voraussetzungen.md#rechner-des-technikers)); das Symbol erscheint dann ohne Neustart des Clients. Im Log steht in dem Fall `Kein Infobereich gefunden`.

**Brauche ich für jeden Kunden einen Sprung-Host?**
Nein, einen je TRMM-Server. Alle Sites teilen ihn; jede hat ihren eigenen Port.

**Kann der Sprung-Host neben TRMM laufen?**
Ja, auf demselben Host oder einem anderen. Er braucht nur einen eigenen Port. Siehe Hairpin in [Eigenes Deployment](../03-installation/07-eigenes-deployment.md).

**Warum nur IPv4?**
Der Sprung-Host prüft die Absenderadresse gegen die öffentliche Adresse der Agenten, und TRMM liefert die nur als IPv4. Über IPv6 ließe sich das nicht prüfen.

**Warum ein eigenes Browserprofil?**
Damit nur dieses Profil durch den Tunnel geht und keine beliebige Webseite aus dem Internet Anfragen in die Kundennetze schicken kann. Das Profil kommt außerhalb der Tunnel nur zum Web Store und zu den Hosts in `direct_hosts`.

**Kann ich Bitwarden oder einen anderen Passwortmanager nutzen?**
Ja, als Erweiterung im Profil, mit dem Server in `direct_hosts`. Siehe [Erweiterungen und Passwortmanager](../04-bedienung/05-erweiterungen.md).

**Warum Brave, Chromium, Chrome oder Edge und nicht Firefox?**
Der Client startet das Profil mit Chromium-Schaltern für Profilordner, Proxy und Zertifikate. Firefox hat dafür keine gleichwertigen Schalter.

**Kann ich die Ziele auch ohne `Manage Sites` pflegen?**
Ja, in TRMM selbst: Site bearbeiten → Custom Fields, im [Format der Felder](../06-referenz/03-site-felder.md). Danach **Neu laden** auf der Steuerseite.

**Wo sind meine Zugangsdaten gespeichert?**
API-Key und CA im Schlüsselbund des Systems, sonst in `~/.local/share/trmm-web-relay/secrets/`. Die Konfigurationsdatei enthält keine Geheimnisse.
