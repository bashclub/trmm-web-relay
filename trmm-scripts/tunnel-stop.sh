#!/usr/bin/env bash
# Web-Relay: Tunnel stoppen (Linux, macOS)
# trmm-web-relay-script 2
#
# Beendet genau den Tunnel der angegebenen Sitzung. Ohne dieses Skript
# endet der Tunnel spätestens mit der TRMM-Laufzeitgrenze.
#
# Argument: <sitzung>

set -u

session=${1:-}
case $session in '' | *[!0-9a-f]*) echo "Ungültige Sitzungskennung" >&2; exit 2 ;; esac

# Nur den ssh-Prozess dieser Sitzung treffen (erkennbar am Schlüsselpfad)
if pkill -f -- "^ssh .*-i /tmp/wr-$session\.[A-Za-z0-9]+/key "; then
	echo "Tunnel $session beendet"
else
	echo "Kein Tunnel $session aktiv"
fi
rm -rf "/tmp/wr-$session".*
exit 0
