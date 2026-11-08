#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
# Sprung-Host starten: Host-Schlüssel anlegen, vertraute CAs übernehmen,
# Sites und erlaubte Absender aus TRMM holen, sshd im Vordergrund starten.
#
# Umgebung:
#   TRUSTED_CA        öffentliche CA-Schlüssel der Clients (Pflicht), mehrere mit ; getrennt;
#                     zusätzlich Dateien /etc/trmm-web-relay/trusted_ca*.pub, falls eingehängt
#   TRMM_URL          TRMM-API (Pflicht): Sites und Absender je Site
#   TRMM_API_KEY_FILE Key nur zum Lesen (/run/secrets/trmm-api-key)
#   ADMIN_FROM        IPv4-Netze, aus denen sich Clients anmelden dürfen (leer: überall)
#   ALLOW_FROM        feste IPv4-Netze, aus denen sich jede Site anmelden darf
#   REFRESH_SECONDS   Abstand des TRMM-Abgleichs (300)
#   SSH_PORT          Port im Container (2222)
#   REMOTE_PORT_BASE  Port je Site: Basis + Site-ID (20000)

set -euo pipefail

state=/run/jumphost
port=${SSH_PORT:-2222}
refresh=${REFRESH_SECONDS:-300}

fail() { echo "Fehler: $*" >&2; exit 1; }

valid_nets() {
	for net in $1; do
		case $net in *[!0-9./]*) fail "ungültiges IPv4-Netz in $2: $net" ;; esac
	done
}
valid_nets "${ADMIN_FROM:-}" ADMIN_FROM
valid_nets "${ALLOW_FROM:-}" ALLOW_FROM
[ -n "${TRMM_URL:-}" ] || fail "TRMM_URL fehlt"

hostkey=/var/lib/jumphost/ssh_host_ed25519_key
if [ ! -f "$hostkey" ]; then
	ssh-keygen -q -t ed25519 -N '' -C jumphost -f "$hostkey"
fi
echo "Host-Schlüssel: $(ssh-keygen -lf "$hostkey.pub")"

mkdir -p /run/sshd "$state/from"
chmod 755 "$state" "$state/from"

# Vertraute CAs: nur Zeilen, die wie öffentliche Schlüssel aussehen
{
	printf '%s\n' "${TRUSTED_CA:-}" | tr ';' '\n'
	cat /etc/trmm-web-relay/trusted_ca*.pub 2>/dev/null || true
} | sed 's/^[[:space:]]*//' |
	grep -E '^(ssh-(ed25519|rsa)|ecdsa-sha2-[a-z0-9]+|sk-[a-z0-9@.-]+) [A-Za-z0-9+/=]+' \
	>"$state/trusted_ca.pub" || true
[ -s "$state/trusted_ca.pub" ] || fail "TRUSTED_CA fehlt (Zeile aus der Einrichtung im Client)"
while read -r line; do
	echo "Vertraute CA: $(printf '%s\n' "$line" | ssh-keygen -lf -)"
done <"$state/trusted_ca.pub"

# Einstellungen für die Hilfsskripte (sshd gibt keine Umgebung weiter)
printf '%s\n' "${REMOTE_PORT_BASE:-20000}" >"$state/port_base"
# shellcheck disable=SC2086 # gewollt: ein Netz je Zeile (oben geprüft)
printf '%s\n' ${ALLOW_FROM:-} >"$state/allow_from"
printf '%s\n' "$TRMM_URL" | sed 's#/*$##' >"$state/trmm_url"
printf '%s\n' "${TRMM_API_KEY_FILE:-/run/secrets/trmm-api-key}" >"$state/trmm_key_file"
chmod 644 "$state"/trusted_ca.pub "$state"/port_base "$state"/allow_from "$state"/trmm_url "$state"/trmm_key_file

# Clients (wr-admin) kommen an alle Tunnel: auf Wunsch nur aus bestimmten Netzen
admins=" wr-admin"
if [ -n "${ADMIN_FROM:-}" ]; then
	admins=""
	for net in $ADMIN_FROM; do admins="$admins wr-admin@$net"; done
	echo "Clients nur aus: $ADMIN_FROM"
fi
echo "AllowUsers wr-tunnel$admins" >"$state/allow.conf"
echo "Feste Netze für alle Sites: ${ALLOW_FROM:-keine}"

# TRMM jetzt und dann regelmäßig abgleichen
/usr/local/sbin/refresh-allowed || true
(while sleep "$refresh"; do /usr/local/sbin/refresh-allowed || true; done) &

# sshd hängt auf stderr \r an jede Zeile; ohne lesen Parser (CrowdSec) sauberer
exec /usr/sbin/sshd -D -e -p "$port" 2> >(sed -u 's/\r$//' >&2)
