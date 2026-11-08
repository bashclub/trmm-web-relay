#!/bin/bash
# SPDX-License-Identifier: GPL-3.0-or-later
# shellcheck disable=SC2016 # eval mit einfachen Anführungszeichen: Variablen erst beim Auswerten
# Handbuch (docs/handbuch): Referenz vollständig, Artikel lassen sich für Outline aufbereiten.
# Ohne Netz, ohne TRMM. Aufruf im Wurzelverzeichnis des Repos: tests/handbuch.sh
repo=$(cd "$(dirname "$0")/.." && pwd)
docs=$repo/docs/handbuch
ref=$docs/06-referenz
count=0 failed=0
check() { ((count++)); if "${@:2}"; then echo "ok   $1"; else echo "FAIL $1"; ((failed++)); fi; }

# jeder Befehl von trmm-web-relay hat einen Abschnitt in der Kommandozeile
cmds=$(grep -oE 'sub\.add_parser\("[a-z-]+"' "$repo/src/trmmwebrelay/cli.py" | cut -d'"' -f2)
for c in $cmds; do
	check "Befehl $c in der Referenz" grep -q "^## \`$c\`\$" "$ref/01-kommandozeile.md"
done

# jede Einstellung (Config und Server) hat einen Abschnitt und eine Zeile in der Übersicht
settings=$(PYTHONPATH="$repo/src" python3 -c '
from dataclasses import fields
from trmmwebrelay.config import Config, Server
print("\n".join(f.name for c in (Config, Server) for f in fields(c) if f.name != "servers"))')
for s in $settings; do
	check "Einstellung $s in der Referenz" grep -q "^### \`$s\`\$" "$ref/02-konfiguration.md"
	check "Einstellung $s in der Übersicht" grep -q "^| \`$s\` |" "$ref/02-konfiguration.md"
done

# jede Variable des Containers (Kopf von entrypoint.sh) hat eine Zeile
vars=$(sed -n '/^# Umgebung:/,/^$/p' "$repo/jumphost/entrypoint.sh" | grep -oE '^#\s+[A-Z_]{4,}' | awk '{print $2}')
for v in $vars; do
	check "Variable $v des Sprung-Hosts" grep -q "^| \`$v\` |" "$ref/04-umgebung-sprunghost.md"
done

# jede Variable des Installers (Kopf von install.sh) hat eine Zeile
vars=$(sed -n '/^# Werte aus der Umgebung/,/^# Optionen/p' "$repo/jumphost/install.sh" | grep -oE '^#\s+[A-Z_]{4,}' | awk '{print $2}')
for v in $vars; do
	check "Variable $v des Installers" grep -q "^| \`$v\` |" "$ref/05-installer-sprunghost.md"
done

# alle Artikel: Kopf, keine Überschrift erster Ebene, Links auf vorhandene Dateien
while IFS=$'\t' read -r file _; do
	check "aufbereitbar: $file" eval '"$docs/render.py" render "$docs/$file" --allow-missing > /dev/null'
done < <("$docs/render.py" list)
check "aufbereitbar: _collection.md" eval '"$docs/render.py" render "$docs/_collection.md" --allow-missing > /dev/null'

# kein Text hinter einem schließenden ``` (Markdown nähme ihn als Sprache des Blocks)
check "kein Text hinter \`\`\`" eval '! grep -rnE "^\`\`\` +[^ ]" "$docs"'

# nichts Internes: nur Beispieldomains
check "nur Beispieldomains" eval '! grep -rnoE "[a-z0-9-]+\.(de|com|net|org|io)\b" "$docs" --include=*.md | grep -vE "example\.(com|org)|bashclub\.org|spille-it\.de|youtube\.com|github\.com|ko-fi\.com|developercertificate\.org|astral\.sh|docs\.astral|nas\.local"'

echo "$((count - failed))/$count bestanden"
[ $failed -eq 0 ]
