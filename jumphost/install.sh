#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
# shellcheck disable=SC1111 # deutsche Anführungszeichen in Meldungen sind gewollt
# Sprung-Host für TRMM Web-Relay installieren oder aktualisieren.
#
# Läuft auf einem Linux-Server mit Podman (ab 4.4, Quadlet), als root oder
# als eigener Dienstbenutzer (rootless). Baut das Image aus diesem Ordner,
# legt den TRMM-Key als Podman-Secret ab, schreibt Quadlet und Einstellungen
# und startet den Dienst. Erneut aufrufen = aktualisieren; vorhandene
# Einstellungen bleiben, neue CAs kommen dazu.
#
# Werte aus der Umgebung (sonst Abfrage):
#   TRMM_URL      TRMM-API, z. B. https://api.example.com
#   TRUSTED_CA    öffentlicher CA-Schlüssel aus der Einrichtung im Client
#   PUBLIC_PORT   Port auf diesem Server (22222)
#   ADMIN_FROM    IPv4-Netze der Techniker (leer: überall), mit Leerzeichen getrennt
#   ALLOW_FROM    feste IPv4-Netze, aus denen jede Site darf (meist leer)
#   TRMM_API_KEY  TRMM-Key nur zum Lesen (List Clients, List Agents); wird abgefragt,
#                 wenn noch kein Secret existiert
#   AUTO_UPDATE   1 (Standard): wöchentlich mit aktuellen Debian-Paketen neu bauen,
#                 Neustart nur bei Änderungen; 0: kein Timer
#
# Optionen: --uninstall (Dienst, Timer und Image entfernen, Host-Schlüssel bleiben)
#           --no-start  (nur Dateien schreiben und Image bauen)
#           --update    (neu bauen, bei neuen Paketen neu starten; ruft der Timer auf)

set -euo pipefail

name=trmm-web-relay-jumphost
secret=trmm-web-relay-api-key
image=localhost/$name
here=$(cd "$(dirname "$0")" && pwd)

die() { echo "Fehler: $*" >&2; exit 1; }
say() { echo "==> $*"; }

start=1
uninstall=0
update=0
for arg in "$@"; do
	case $arg in
	--no-start) start=0 ;;
	--uninstall) uninstall=1 ;;
	--update) update=1 ;;
	-h | --help) sed -n '3,24p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
	*) die "unbekannte Option $arg" ;;
	esac
done

command -v podman >/dev/null || die "Podman fehlt (z. B. apt install podman / dnf install podman)"
ver=$(podman version --format '{{.Client.Version}}' 2>/dev/null || podman --version | awk '{print $3}')
major=${ver%%.*}
minor=${ver#*.}; minor=${minor%%.*}
if [ "$major" -lt 4 ] || { [ "$major" -eq 4 ] && [ "$minor" -lt 4 ]; }; then
	die "Podman $ver ist zu alt, Quadlet braucht 4.4 oder neuer"
fi

if [ "$(id -u)" -eq 0 ]; then
	unitdir=/etc/containers/systemd
	confdir=/etc/trmm-web-relay
	sysctl=(systemctl)
	wanted=multi-user.target
	sysunitdir=/etc/systemd/system
else
	unitdir=${XDG_CONFIG_HOME:-$HOME/.config}/containers/systemd
	confdir=${XDG_CONFIG_HOME:-$HOME/.config}/trmm-web-relay
	sysctl=(systemctl --user)
	wanted=default.target
	sysunitdir=${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user
fi
envfile=$confdir/jumphost.env
unit=$unitdir/$name.container
# Quellen des Images bleiben hier liegen, damit der Timer neu bauen kann
srcdir=$confdir/src
updater=$name-update
FILES="Containerfile sshd_config entrypoint.sh refresh-allowed.sh principals.sh install.sh"

remove_updater() {
	"${sysctl[@]}" disable --now "$updater.timer" 2>/dev/null || true
	rm -f "${sysunitdir:?}/${updater:?}.service" "${sysunitdir:?}/${updater:?}.timer"
}

# Installierte Pakete eines Images, zum Vergleich vor einem Neustart
packages() {
	# shellcheck disable=SC2016 # Platzhalter für dpkg-query, nicht für die Shell
	podman run --rm --entrypoint dpkg-query "$1" -W -f '${Package} ${Version}\n' 2>/dev/null
}

if [ "$update" -eq 1 ]; then
	[ -e "$unit" ] && [ -r "$srcdir/Containerfile" ] || die "nicht installiert (erst ohne --update ausführen)"
	say "Image mit aktuellen Paketen bauen"
	podman build -q --pull=newer --no-cache -t "$image:candidate" "$srcdir" >/dev/null
	old_id=$(podman image inspect --format '{{.Id}}' "$image" 2>/dev/null || true)
	if [ -n "$old_id" ] && [ "$(packages "$image:candidate")" = "$(packages "$image")" ]; then
		podman rmi "$image:candidate" >/dev/null
		say "Keine neuen Pakete, kein Neustart"
		exit 0
	fi
	podman tag "$image:candidate" "$image"
	podman rmi "$image:candidate" >/dev/null
	"${sysctl[@]}" restart "$name.service"
	if [ -n "$old_id" ]; then podman rmi "$old_id" >/dev/null 2>&1 || true; fi
	say "Aktualisiert und neu gestartet"
	exit 0
fi

if [ "$uninstall" -eq 1 ]; then
	remove_updater
	"${sysctl[@]}" stop "$name.service" 2>/dev/null || true
	rm -f "$unit"
	rm -rf "${srcdir:?}"
	"${sysctl[@]}" daemon-reload
	podman rmi -f "$image" >/dev/null 2>&1 || true
	podman secret rm "$secret" >/dev/null 2>&1 || true
	say "Entfernt. Einstellungen ($envfile) und Volume $name (Host-Schlüssel) bleiben;"
	say "ganz löschen: rm $envfile && podman volume rm $name"
	exit 0
fi

# Vorhandene Einstellungen lesen (Format: KEY=Wert, ohne Anführungszeichen)
old() { [ -r "$envfile" ] && sed -n "s/^$1=//p" "$envfile" | tail -1 || true; }

ask() { # ask VAR "Frage" [Vorgabe]
	local var=$1 prompt=$2 def=${3:-} value
	value=${!var:-}
	if [ -z "$value" ] && [ -t 0 ]; then
		read -r -p "$prompt${def:+ [$def]}: " value
	fi
	printf -v "$var" '%s' "${value:-$def}"
}

ask TRMM_URL "TRMM-API-Adresse" "$(old TRMM_URL)"
[ -n "$TRMM_URL" ] || die "TRMM_URL fehlt"
case $TRMM_URL in https://*) ;; *) die "TRMM_URL muss mit https:// beginnen" ;; esac

# CAs zusammenführen: vorhandene behalten, neue dazu
cas=$( { old TRUSTED_CA | tr ';' '\n'; printf '%s\n' "${TRUSTED_CA:-}" | tr ';' '\n'; } |
	sed 's/^[[:space:]]*//;s/[[:space:]]*$//' | grep -E '^(ssh-|ecdsa-|sk-)' | awk '!seen[$1" "$2]++' || true)
if [ -z "$cas" ]; then
	ask TRUSTED_CA "Öffentlicher CA-Schlüssel (aus der Einrichtung im Client)"
	cas=$(printf '%s\n' "$TRUSTED_CA" | tr ';' '\n' | grep -E '^(ssh-|ecdsa-|sk-)' || true)
fi
[ -n "$cas" ] || die "TRUSTED_CA fehlt"

PUBLIC_PORT=${PUBLIC_PORT:-$(old PUBLIC_PORT)}
PUBLIC_PORT=${PUBLIC_PORT:-22222}
case $PUBLIC_PORT in '' | *[!0-9]*) die "PUBLIC_PORT ungültig" ;; esac
if [ -z "${ADMIN_FROM+x}" ] && [ ! -e "$envfile" ] && [ -t 0 ]; then
	read -r -p "IPv4-Netze der Techniker, z. B. 203.0.113.7/32 10.8.0.0/24 (leer: überall): " ADMIN_FROM
fi
ADMIN_FROM=${ADMIN_FROM-$(old ADMIN_FROM)}
ALLOW_FROM=${ALLOW_FROM-$(old ALLOW_FROM)}
for net in $ADMIN_FROM $ALLOW_FROM; do
	case $net in *[!0-9./]*) die "kein IPv4-Netz: $net" ;; esac
done

if ! podman secret inspect "$secret" >/dev/null 2>&1 || [ -n "${TRMM_API_KEY:-}" ]; then
	if [ -z "${TRMM_API_KEY:-}" ]; then
		[ -t 0 ] || die "TRMM_API_KEY fehlt"
		read -r -s -p "TRMM-API-Key nur zum Lesen (Rechte: List Clients, List Agents): " TRMM_API_KEY
		echo
	fi
	[ -n "$TRMM_API_KEY" ] || die "TRMM-API-Key fehlt"
	podman secret rm "$secret" >/dev/null 2>&1 || true
	printf '%s' "$TRMM_API_KEY" | podman secret create "$secret" - >/dev/null
	unset TRMM_API_KEY
	say "TRMM-Key als Podman-Secret $secret abgelegt"
fi

mkdir -p "$confdir" "$unitdir"
umask 022
if [ "$here" != "$srcdir" ]; then
	rm -rf "${srcdir:?}.new"
	mkdir -p "$srcdir.new"
	for f in $FILES; do cp "$here/$f" "$srcdir.new/$f"; done
	rm -rf "${srcdir:?}"
	mv "$srcdir.new" "$srcdir"
fi

say "Image bauen"
podman build -q --pull=newer -t "$image" "$srcdir" >/dev/null

{
	echo "# TRMM Web-Relay Sprung-Host (geschrieben von install.sh; Format: KEY=Wert ohne Anführungszeichen)"
	echo "TRMM_URL=$TRMM_URL"
	echo "TRUSTED_CA=$(printf '%s\n' "$cas" | paste -sd ';' -)"
	echo "ADMIN_FROM=$ADMIN_FROM"
	echo "ALLOW_FROM=$ALLOW_FROM"
	echo "PUBLIC_PORT=$PUBLIC_PORT"
} >"$envfile.new"
mv "$envfile.new" "$envfile"

cat >"$unit" <<EOF
# TRMM Web-Relay Sprung-Host (geschrieben von install.sh)
[Unit]
Description=TRMM Web-Relay Sprung-Host
After=network-online.target
Wants=network-online.target

[Container]
ContainerName=$name
Image=$image
PublishPort=$PUBLIC_PORT:2222
EnvironmentFile=$envfile
Secret=$secret,target=trmm-api-key
Volume=$name:/var/lib/jumphost:Z
RunInit=true
LogDriver=journald
LogOpt=tag=sshd

[Service]
Restart=always

[Install]
WantedBy=$wanted
EOF
say "Quadlet $unit und Einstellungen $envfile geschrieben"

AUTO_UPDATE=${AUTO_UPDATE:-1}
if [ "$AUTO_UPDATE" = 1 ]; then
	mkdir -p "$sysunitdir"
	cat >"$sysunitdir/$updater.service" <<EOF
# TRMM Web-Relay Sprung-Host: Image neu bauen (geschrieben von install.sh)
[Unit]
Description=TRMM Web-Relay Sprung-Host aktualisieren
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
ExecStart=/bin/bash $srcdir/install.sh --update
EOF
	cat >"$sysunitdir/$updater.timer" <<EOF
# TRMM Web-Relay Sprung-Host: wöchentlich aktualisieren (geschrieben von install.sh)
[Unit]
Description=TRMM Web-Relay Sprung-Host wöchentlich aktualisieren

[Timer]
OnCalendar=Sun *-*-* 04:00
RandomizedDelaySec=2h
Persistent=true

[Install]
WantedBy=timers.target
EOF
	say "Auto-Update: $updater.timer (sonntags, Neustart nur bei neuen Paketen)"
else
	remove_updater
	say "Auto-Update aus (AUTO_UPDATE=0)"
fi

if [ "$start" -eq 0 ]; then
	say "Nicht gestartet (--no-start). Start: ${sysctl[*]} daemon-reload && ${sysctl[*]} start $name.service"
	exit 0
fi
if [ "$(id -u)" -ne 0 ] && command -v loginctl >/dev/null; then
	loginctl enable-linger "$(id -un)" 2>/dev/null ||
		echo "Hinweis: „loginctl enable-linger $(id -un)“ als root ausführen, sonst endet der Dienst beim Abmelden"
fi
"${sysctl[@]}" daemon-reload
"${sysctl[@]}" restart "$name.service"
if [ "$AUTO_UPDATE" = 1 ]; then
	"${sysctl[@]}" enable --now "$updater.timer" >/dev/null
fi

for _ in $(seq 1 20); do
	fp=$(podman logs "$name" 2>/dev/null | sed -n 's/^Host-Schlüssel: //p' | tail -1)
	[ -n "$fp" ] && break
	sleep 1
done
podman logs "$name" 2>&1 | tail -n 20
echo
if [ -z "$fp" ]; then
	die "Dienst läuft nicht richtig, siehe oben bzw. „podman logs $name“"
fi
say "Fertig. Der Sprung-Host lauscht auf TCP $PUBLIC_PORT (nur IPv4)."
say "Fingerabdruck zum Vergleich im Client: $fp"
say "Firewall/Portweiterleitung: TCP $PUBLIC_PORT von außen auf diesen Server freigeben."
