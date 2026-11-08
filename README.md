# TRMM Web-Relay

[Deutsch](README.de.md)

> Development takes place at https://code.bashclub.org/bashclub/trmm-web-relay
>
> Handbook (German, no login required): https://docs.bashclub.org/s/trmm-web-relay

Open web interfaces in customer networks on demand, without permanent VPN tunnels. One click on the local control page makes [Tactical RMM](https://github.com/amidaware/tacticalrmm) start a time-limited reverse SOCKS tunnel on an agent at the customer site. A dedicated browser profile then opens the real address of the target, e.g. `https://192.168.1.1`.

- **Nothing stays open**: the tunnel exists only during the session and ends after idle time (30 min), after 4 h at most, or on "Beenden" (stop).
- **No VPN server and no port forwarding at the customer**: the TRMM agent connects outbound to a jump host run by the MSP.
- **Short-lived certificates**: the client signs throwaway keys for 15 minutes per session; the jump host checks site, port and source IP.
- **Browser only**: a dedicated browser profile talks to a local SOCKS router that only lets targets of active sessions through. Overlapping address ranges at different customers are no problem.
- **Targets live in TRMM**: web sites and preferred tunnel agents are two custom fields on the site, edited on the control page. No second inventory.
- **Several TRMM servers** per client, one at a time.

Agents: Linux and macOS (Windows planned). Client: Linux, macOS, Windows (Windows and macOS less tested). Jump host: Linux server with Podman 4.4 or newer.

## Quick start

1. **Install the client** (needs the OpenSSH client and Brave, Chromium, Chrome or Edge):
   ```sh
   git clone https://code.bashclub.org/bashclub/trmm-web-relay.git
   sh trmm-web-relay/install/client.sh
   ```
   On Windows: `powershell -ExecutionPolicy Bypass -File trmm-web-relay\install\client.ps1`
2. **Prepare TRMM**: create a user and role for the client (permissions `List Clients`, `List Agents`, `View Custom Fields`, `List Scripts`, `Run Scripts`; for the setup also `Manage Custom Fields`, `Manage Scripts`, `Manage Sites`) and an API key for that user.
3. **Setup**: double-click "TRMM Web-Relay", add the server, click "Prüfen" (check) and work through the steps (create fields and scripts in TRMM, create the CA).
4. **Jump host**: download the installer in the setup and run it on a Linux server with Podman (`bash trmm-web-relay-sprunghost-*.sh`), open TCP 22222, confirm the fingerprint in the client.
5. **Use it**: on the control page click "Bearbeiten" (edit) at a site, enter the web sites, click "Verbinden" (connect).

The user interface and the handbook are in German for now.

## Commands

```
trmm-web-relay            # start the client (like the double-click)
trmm-web-relay check      # check the setup of all servers (read-only)
trmm-web-relay targets    # show targets and tunnel agents from TRMM
trmm-web-relay desktop    # create the launcher (--remove: remove it)
```

## License and contributing

GPL-3.0-or-later. Bugs, questions and wishes as issues on https://code.bashclub.org/bashclub/trmm-web-relay, contributions see `CONTRIBUTING.md`.

Maintainer: Thorsten Spille, [Spille IT Solutions](https://spille-it.de), bashclub.
