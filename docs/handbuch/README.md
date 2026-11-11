# Handbuch TRMM Web-Relay: Regeln für Autoren

Das Handbuch entsteht hier im Repo und wird nach Outline veröffentlicht:
- öffentlich, ohne Login: https://docs.bashclub.org/s/trmm-web-relay
- mit Login (für Autoren beim Veröffentlichen): (Adresse steht in `_collection.md`, Feld `outline`)

**Git ist die Quelle.** Änderungen direkt in Outline werden beim nächsten Veröffentlichen überschrieben. Jede Seite
in Outline endet mit einem Link auf ihre Datei hier.

## Aufbau
- Ein Ordner je Bereich (`01-schnellstart`, `02-konzept`, …), die Nummer bestimmt die Reihenfolge.
- `_index.md` im Ordner ist die Seite des Bereichs in Outline, die Artikel des Ordners hängen darunter.
- Artikel heißen `NN-name.md`, die Nummer bestimmt die Reihenfolge im Bereich.
- `_collection.md` ist die Beschreibung der Collection (Startseite des Handbuchs mit der Liste der Kapitel). Ein neuer
  Bereich kommt dort dazu.

Jede Datei beginnt mit einem Kopf:
```
---
title: Architektur und Ablauf eines Laufs
audience: Admin
outline:
---
```
- `title`: Titel in Outline. Der Text beginnt ohne Überschrift erster Ebene (`#`), Outline zeigt den Titel selbst.
- `audience`: `Anwender`, `Admin` oder `Anwender, Admin`.
- `outline`, `outline_id`: Adresse und ID der Seite in Outline, beim ersten Veröffentlichen eingetragen.

## Versionen
Das Handbuch beschreibt die aktuelle Version (siehe `_collection.md`). Neue Funktionen nennen ab der ersten veröffentlichten Version danach die Version, mit der sie kamen, im ersten Satz des Abschnitts: „Ab 0.3 …“. Geänderter Betrieb steht in einer Hinweisbox mit altem und neuem Verhalten und was der Admin tun muss:
```
:::info
**Geändert in 0.3:** Bis 0.2 … Ab 0.3 … Bestehende Installationen …
:::
```

## Befehle
- **Copy & Paste-fest:** keine Platzhalter wie `<pool>` und kein „ersetze X“. Werte, die das System liefert,
  ermittelt der Befehl selbst (z. B. der Mountpoint eines Volumes per `podman volume inspect`). Wo der Admin einen Wert wählen muss, steht er als Variable in der ersten Zeile des Blocks.
- Codeblöcke mit Sprache (`bash`), ein Befehl pro Zeile, Ausgaben getrennt davon.
- Befehle, die etwas löschen, nennen vorher, was bleibt.
- Beispiele ohne echte Kunden, Hostnamen oder Adressen: `example.com`, Dokumentationsnetze (`192.0.2.0/24`,
  `198.51.100.0/24`, `203.0.113.0/24`), private Netze wie `192.168.1.0/24`.
- Snippets werden vor dem Veröffentlichen in einem Container oder auf der Test-VM ausgeführt.

## Sprache und Stil
- Deutsch zuerst; die englische Collection folgt, wenn die deutschen Artikel stehen.
- Kurze Sätze, eine Aussage pro Satz, Fachbegriffe beim ersten Auftreten erklären (siehe Glossar).
- Programme, Parameter, Dateien und Properties in `Code`.

## Links
- Auf andere Artikel relativ verlinken: `[Sicherheitsmodell](../02-konzept/03-sicherheitsmodell.md)`, auch mit Anker
  (`…md#abschnitt`). Beim Veröffentlichen werden daraus die Adressen in Outline.
- Auf Tickets mit voller Adresse, nur wenn sie dem Leser weiterhelfen.

## Veröffentlichen
`render.py` bereitet eine Datei für Outline auf: Kopf entfernt, Links auf Outline-Adressen, am Ende ein Link
„Weiter“ auf den nächsten Artikel in der Reihenfolge von `render.py list` (nach dem letzten Artikel eines Bereichs der
nächste Bereich), der Hinweis auf die Quelle; davor der Ko-fi-Block (Tabelle mit einer zentrierten Spalte:
`kofi-block.png` mit Frage und Knopf, darunter der Link). Die Bilder (`kofi-block.png`, `kofi-button.png`, englisch
`kofi-button-en.png` für die README) zeichnet `kofi-button.py` im Stil des Ko-fi-Widgets, mit Text, Farbe und Frage
als Argumenten. Den Block für dieses Handbuch erzeugt:
```bash
docs/handbuch/kofi-button.py docs/handbuch/kofi-block.png "Unterstütze die Entwicklung" "#E67224" "Gefällt dir TRMM Web-Relay?"
```
Aufbereiten:
```bash
docs/handbuch/render.py list
docs/handbuch/render.py render docs/handbuch/02-konzept/02-ablauf.md
```
Veröffentlicht wird per CI (`.forgejo/workflows/handbuch.yml`, `ci.sh`): Jeder Push auf `main`, der das Handbuch
ändert, aktualisiert die Seiten, deren aufbereiteter Text sich geändert hat (`render.py publish --since <vorher>`), auch
die Beschreibung der Collection aus `_collection.md`. Ein Pull Request zeigt nur, welche Seiten sich ändern würden. Von
Hand gestartet („Run workflow“) gehen alle Seiten raus. Lokal prüfen, was ginge:
```bash
docs/handbuch/render.py publish --since origin/main --dry-run
```
Die CI legt keine Seiten an und verschiebt keine. Neue Artikel deshalb zuerst von Hand anlegen und einordnen (unten).
Ein neuer Artikel wird zuerst angelegt und seine Adresse in `outline:` eingetragen, danach werden Links auf ihn
aufgelöst. `_collection.md` geht ohne den Hinweis am Ende in die Beschreibung der Collection. Ein neuer, verschobener
oder umbenannter Artikel ändert den Link „Weiter“ seines Vorgängers: den Vorgänger mit veröffentlichen.

Reihenfolge: Outline setzt neue Seiten an eine beliebige Stelle ihrer Ebene (meist an den Anfang). Nach dem Anlegen
deshalb **alle** Seiten des betroffenen Bereichs und den Bereich selbst an ihre Position schieben, nicht nur die neue
Seite; eine Seite in der Mitte verschiebt die folgenden. `render.py list` liefert dafür je Zeile in Spalte 5 die
Position (0-basiert, `index` von `move_document`), in Spalte 6 die eigene ID und in Spalte 7 die ID des Elternteils
(für einen Bereich die Collection, sonst die `_index.md` des Bereichs):
```bash
docs/handbuch/render.py list | awk -F'\t' '{ print $5, $6, $7, $1 }'
```
Die Positionen in aufsteigender Reihenfolge setzen (erst 0, dann 1, …). Zum Schluss mit `list_collection_documents`
gegen `render.py list` prüfen. Links auf noch nicht veröffentlichte Artikel bricht `render` ab (`--allow-missing` lässt nur den Text
stehen).

## Prüfung
`tests/handbuch.sh` prüft ohne Netz und ohne TRMM: Jeder Befehl von `trmm-web-relay` hat einen Abschnitt
`` ## `name` `` in der Kommandozeile (`06-referenz/01-kommandozeile.md`), jede Einstellung der Konfiguration einen
Abschnitt `` ### `name` `` und eine Zeile in der Übersicht (`02-konfiguration.md`), jede Variable des Containers eine
Zeile in `04-umgebung-sprunghost.md` und jede Variable des Installers eine Zeile in `05-installer-sprunghost.md`. Dazu
muss sich jeder Artikel aufbereiten lassen. Die Referenz wird von Hand gepflegt; die Prüfung fällt auf, wenn etwas
Neues fehlt.

## Definition of Done
Eine Änderung an Verhalten, Einstellungen, Befehlen oder Meldungen aktualisiert die betroffenen Artikel (Konzept,
Anleitung, Referenz, Fehlerbehebung) im selben PR, mit Versionsvermerk.
