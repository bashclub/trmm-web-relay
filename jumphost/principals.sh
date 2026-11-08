#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-or-later
# AuthorizedPrincipalsCommand für sshd: erlaubte Principals eines Kontos.
#
# Agenten melden sich als wr-tunnel mit einem Zertifikat für „site-<id>“ an.
# Je Site gibt es eine Zeile mit ihrem Port (permitlisten) und den erlaubten
# Absendern (from): öffentliche IPv4 der Agenten dieser Site, die in TRMM
# online sind, und die festen Netze aus ALLOW_FROM. Sites ohne erlaubten
# Absender fehlen, ihre Anmeldung scheitert.

set -eu

user=${1:-}
state=/run/jumphost

case $user in
wr-admin)
	echo 'restrict,port-forwarding,permitopen="127.0.0.1:*" wr-admin'
	;;
wr-tunnel)
	base=$(cat "$state/port_base")
	allow=$(grep -v '^$' "$state/allow_from" 2>/dev/null | paste -sd, -) || true
	[ -r "$state/sites" ] || exit 0
	while read -r id; do
		case $id in '' | *[!0-9]*) continue ;; esac
		from=$(cat "$state/from/$id" 2>/dev/null | grep -v '^$' | paste -sd, -) || true
		[ -n "$allow" ] && from=${from:+$from,}$allow
		[ -n "$from" ] || continue
		echo "restrict,port-forwarding,permitlisten=\"127.0.0.1:$((base + id))\",from=\"$from\" site-$id"
	done <"$state/sites"
	;;
esac
