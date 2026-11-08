#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
# Sites und erlaubte Absender aus TRMM holen. Ergebnis:
#   /run/jumphost/sites           alle Site-IDs (eine je Zeile)
#   /run/jumphost/from/<site-id>  öffentliche IPv4 der Agenten dieser Site,
#                                 die gerade online sind
#
# Schlägt die Abfrage fehl, bleibt die letzte Liste stehen.

set -euo pipefail

state=/run/jumphost
url=$(cat "$state/trmm_url")
keyfile=$(cat "$state/trmm_key_file")
[ -r "$keyfile" ] || { echo "TRMM-Abgleich: Key fehlt ($keyfile)" >&2; exit 1; }

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

get() {
	curl -fsS --max-time 30 -H "Accept: application/json" \
		-H @<(printf 'X-API-KEY: %s\n' "$(tr -d '\n' <"$keyfile")") \
		"$url$1"
}

if ! get "/clients/" >"$tmp/clients.json" || ! get "/agents/" >"$tmp/agents.json"; then
	echo "TRMM-Abgleich fehlgeschlagen, letzte Liste bleibt" >&2
	exit 1
fi

jq -r '.[].sites[].id' "$tmp/clients.json" | sort -n >"$tmp/sites"

# Zuordnung (Kunde, Site) -> Site-ID, dann je Site die IPv4-Adressen der Agenten online
mkdir -p "$tmp/from"
jq -r --slurpfile c "$tmp/clients.json" '
	($c[0] | map(.name as $cl | .sites[] | {("\($cl)\u0000\(.name)"): .id}) | add) as $site
	| .[]
	| select(.status == "online")
	| select((.public_ip // "") | test("^[0-9]{1,3}(\\.[0-9]{1,3}){3}$"))
	| "\($site["\(.client_name)\u0000\(.site_name)"]) \(.public_ip)"
' "$tmp/agents.json" | sort -u | while read -r site ip; do
	case $site in '' | *[!0-9]*) continue ;; esac
	echo "$ip" >>"$tmp/from/$site"
done

# Alle IPv4-Adressen von Agenten (auch offline) für eine Allowlist außerhalb,
# z. B. CrowdSec auf der Firewall: eine Sperre dort würde auch TRMM für den Kunden trennen
jq -r '.[] | (.public_ip // "") | select(test("^[0-9]{1,3}(\\.[0-9]{1,3}){3}$"))' "$tmp/agents.json" |
	sort -u >"$tmp/agent-ipv4.txt"
mkdir -p /var/lib/jumphost/export
if ! cmp -s "$tmp/agent-ipv4.txt" /var/lib/jumphost/export/agent-ipv4.txt; then
	install -m 644 "$tmp/agent-ipv4.txt" /var/lib/jumphost/export/agent-ipv4.txt.new
	mv /var/lib/jumphost/export/agent-ipv4.txt.new /var/lib/jumphost/export/agent-ipv4.txt
	echo "Agenten-Adressen für Allowlist: $(wc -l <"$tmp/agent-ipv4.txt")"
fi

# Austauschen und Änderungen ins Log
if ! cmp -s "$tmp/sites" "$state/sites"; then
	echo "Sites in TRMM: $(wc -l <"$tmp/sites")"
	install -m 644 "$tmp/sites" "$state/sites.new"
	mv "$state/sites.new" "$state/sites"
fi
mkdir -p "$state/from"
for f in "$tmp"/from/*; do
	[ -e "$f" ] || continue
	site=$(basename "$f")
	if ! cmp -s "$f" "$state/from/$site"; then
		echo "Site $site: erlaubte Absender $(paste -sd, "$f")"
	fi
	install -m 644 "$f" "$state/from/$site.new"
	mv "$state/from/$site.new" "$state/from/$site"
done
for f in "$state"/from/*; do
	[ -e "$f" ] || continue
	site=$(basename "$f")
	if [ ! -e "$tmp/from/$site" ]; then
		echo "Site $site: kein Agent online, keine Absender aus TRMM"
		rm -f "$f"
	fi
done
