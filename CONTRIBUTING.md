# Mitarbeit

Beiträge sind willkommen, als Issue oder Pull Request auf https://code.bashclub.org/bashclub/trmm-web-relay. Zum Kommentieren ist ein Konto bei code.bashclub.org nötig, die Anmeldung geht auch mit einem GitHub-Konto.

## Lizenz und Developer Certificate of Origin

TRMM Web-Relay steht unter der GNU General Public License, Version 3 oder später (`GPL-3.0-or-later`). Mit einem Beitrag stimmst du zu, dass er unter dieser Lizenz veröffentlicht wird.

Jeder Commit braucht eine Zeile `Signed-off-by` (`git commit -s`). Damit bestätigst du das [Developer Certificate of Origin 1.1](https://developercertificate.org/): Du hast den Beitrag selbst geschrieben oder darfst ihn unter der Lizenz des Projekts einreichen.

Neue Dateien beginnen mit der Lizenzkennung:
~~~
# SPDX-License-Identifier: GPL-3.0-or-later
~~~
Ausnahme: die Skripte in `trmm-scripts/`. Der Client vergleicht sie mit den Skripten in TRMM; jede Änderung macht sie dort „veraltet“. Für sie gilt die Lizenz über `LICENSE`.

## Änderungen

- Doku, Commits und Kommentare auf Deutsch, Bezeichner auf Englisch.
- Bestehende Installationen laufen nach einem Update weiter. Ändern sich Skripte für die Agenten, zeigt die Einrichtung sie als veraltet und aktualisiert sie nach Rückfrage. Ändert sich der Sprung-Host, braucht es einen neuen Installer aus dem Client.
- Keine Geheimnisse, Kundennamen oder internen Adressen in Code, Doku oder Tests. Beispiele mit `example.com` und Dokumentationsnetzen.
- Das Handbuch (`docs/handbuch/`) wird im selben Pull Request nachgezogen; Regeln für Autoren in `docs/handbuch/README.md`. `tests/handbuch.sh` prüft, dass Befehle, Einstellungen und Variablen des Sprung-Hosts in der Referenz stehen.
- Shell-Skripte ohne Befunde von `shellcheck`.
