#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-or-later
# shellcheck disable=SC1111 # deutsche Anführungszeichen in Meldungen sind gewollt
# TRMM Web-Relay: Client installieren oder aktualisieren (Linux, macOS).
#
# Installiert bei Bedarf uv (bringt ein passendes Python mit), dann den
# Client als eigenständiges Werkzeug und legt das Startsymbol an.
# Danach: Doppelklick auf „TRMM Web-Relay“, die Einrichtung öffnet sich.
#
# Quelle: Ordner dieses Repos (Standard) oder WR_SOURCE, z. B.
#   WR_SOURCE=git+https://git.example.com/msp/trmm-web-relay sh client.sh
# Voraussetzungen: ssh (OpenSSH-Client) und Brave, Chromium, Chrome oder Edge.

set -eu

here=$(cd "$(dirname "$0")/.." && pwd)
source=${WR_SOURCE:-$here}

command -v ssh >/dev/null || { echo "Fehler: OpenSSH-Client (ssh) fehlt" >&2; exit 1; }

if ! command -v uv >/dev/null; then
	PATH=$HOME/.local/bin:$PATH
fi
if ! command -v uv >/dev/null; then
	echo "==> uv installieren (https://astral.sh/uv)"
	if command -v curl >/dev/null; then
		curl -LsSf https://astral.sh/uv/install.sh | sh
	else
		wget -qO- https://astral.sh/uv/install.sh | sh
	fi
	PATH=$HOME/.local/bin:$PATH
fi

echo "==> TRMM Web-Relay installieren aus $source"
uv tool install --force "$source"

bin=$(uv tool dir --bin)/trmm-web-relay
echo "==> Startsymbol anlegen"
"$bin" desktop
echo
echo "Fertig. Start per Doppelklick auf „TRMM Web-Relay“ (Desktop bzw. Programme),"
echo "oder im Terminal: $bin"
