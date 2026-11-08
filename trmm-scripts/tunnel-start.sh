#!/usr/bin/env bash
# Web-Relay: Tunnel starten (Linux, macOS)
# trmm-web-relay-script 2
#
# Baut einen Reverse-SOCKS-Tunnel zum Sprung-Host auf: dort lauscht dann
# 127.0.0.1:<fernport>, und jede Verbindung darüber geht von diesem Gerät
# aus ins Kundennetz.
#
# Start über TRMM im Modus „nicht warten“ mit Laufzeitgrenze. ssh läuft
# als direktes Kind dieses Skripts (nicht abgekoppelt), damit der Agent es
# bei Ablauf der Grenze mitbeendet.
#
# Argumente: <sitzung> <sprunghost> <port> <konto> <fernport>
# Umgebung:  WR_KEY          Wegwerf-Schlüssel, base64
#            WR_CERT         Zertifikat dazu (wenige Minuten gültig), base64
#            WR_KNOWN_HOSTS  Host-Schlüssel des Sprung-Hosts (known_hosts-Zeilen), base64

set -u

if [ "$#" -ne 5 ]; then
	echo "Aufruf: <sitzung> <sprunghost> <port> <konto> <fernport>" >&2
	exit 2
fi
session=$1 host=$2 port=$3 user=$4 rport=$5

case $session in '' | *[!0-9a-f]*) echo "Ungültige Sitzungskennung" >&2; exit 2 ;; esac
case $port in '' | *[!0-9]*) echo "Ungültiger Port" >&2; exit 2 ;; esac
case $rport in '' | *[!0-9]*) echo "Ungültiger Fernport" >&2; exit 2 ;; esac
case $host in '' | -* | *[!A-Za-z0-9.:_-]*) echo "Ungültiger Sprung-Host" >&2; exit 2 ;; esac
case $user in '' | -* | *[!A-Za-z0-9._-]*) echo "Ungültiges Konto" >&2; exit 2 ;; esac
if [ -z "${WR_KEY:-}" ] || [ -z "${WR_CERT:-}" ] || [ -z "${WR_KNOWN_HOSTS:-}" ]; then
	echo "WR_KEY, WR_CERT oder WR_KNOWN_HOSTS fehlt" >&2
	exit 2
fi
command -v ssh >/dev/null || { echo "ssh fehlt" >&2; exit 3; }

umask 077
# Der Pfad enthält die Sitzung; daran findet das Stopp-Skript den ssh-Prozess.
dir=$(mktemp -d "/tmp/wr-$session.XXXXXX") || exit 1
pid=""
trap 'rm -rf "$dir"' EXIT
trap '[ -n "$pid" ] && kill "$pid" 2>/dev/null; exit 0' TERM INT HUP

printf '%s' "$WR_KEY" | base64 -d >"$dir/key" 2>/dev/null ||
	printf '%s' "$WR_KEY" | base64 -D >"$dir/key" # ältere macOS
printf '%s' "$WR_CERT" | base64 -d >"$dir/key-cert.pub" 2>/dev/null ||
	printf '%s' "$WR_CERT" | base64 -D >"$dir/key-cert.pub"
printf '%s' "$WR_KNOWN_HOSTS" | base64 -d >"$dir/known_hosts" 2>/dev/null ||
	printf '%s' "$WR_KNOWN_HOSTS" | base64 -D >"$dir/known_hosts"
unset WR_KEY WR_CERT WR_KNOWN_HOSTS

ssh -N -T -F /dev/null \
	-i "$dir/key" -o CertificateFile="$dir/key-cert.pub" -o IdentitiesOnly=yes -o IdentityAgent=none \
	-o UserKnownHostsFile="$dir/known_hosts" -o GlobalKnownHostsFile=/dev/null \
	-o StrictHostKeyChecking=yes -o BatchMode=yes -o ConnectTimeout=15 \
	-o ExitOnForwardFailure=yes -o ServerAliveInterval=15 -o ServerAliveCountMax=3 \
	-o PermitLocalCommand=yes -o LocalCommand="rm -f $dir/key $dir/key-cert.pub" \
	-4 -p "$port" -R "127.0.0.1:$rport" "$user@$host" </dev/null &
pid=$!

# Schlüssel spätestens nach 30 s löschen, auch wenn LocalCommand nicht lief.
# Das Zertifikat ist ohnehin nur wenige Minuten gültig.
for _ in $(seq 1 30); do
	[ -e "$dir/key" ] || break
	kill -0 "$pid" 2>/dev/null || break
	sleep 1
done
rm -f "$dir/key" "$dir/key-cert.pub"

wait "$pid"
rc=$?
echo "Tunnel $session beendet (ssh-Status $rc)"
exit "$rc"
