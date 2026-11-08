# SPDX-License-Identifier: GPL-3.0-or-later
"""Startsymbol auf dem Desktop und im Startmenü (Linux, macOS, Windows).

Der Doppelklick startet den Client ohne Terminal; läuft er schon, öffnet
sich nur die Steuerseite.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

from trmmwebrelay.platform import MACOS, PACKAGE_DIR, WINDOWS, quiet

APP_NAME = "TRMM Web-Relay"
ICON = PACKAGE_DIR / "static" / "icon.svg"


def _command() -> tuple[str, list[str], dict]:
    """Programm, Argumente und Umgebung für den Start ohne Terminal."""
    exe = sys.executable
    if WINDOWS:
        w = Path(exe).with_name("pythonw.exe")
        if w.exists():
            exe = str(w)
    env = {}
    # Aus dem Repo gestartet (nicht installiert): Paketpfad mitgeben
    clean = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    r = subprocess.run(
        [sys.executable, "-c", "import trmmwebrelay; print(trmmwebrelay.__file__)"],
        capture_output=True, text=True, check=False, env=clean, cwd=Path.home(), **quiet(),
    )
    if r.returncode != 0 or Path(r.stdout.strip()).parent.resolve() != PACKAGE_DIR.resolve():
        env["PYTHONPATH"] = str(PACKAGE_DIR.parent)
    return exe, ["-m", "trmmwebrelay"], env


def _desktop_dir() -> Path:
    if not WINDOWS and not MACOS and shutil.which("xdg-user-dir"):
        r = subprocess.run(["xdg-user-dir", "DESKTOP"], capture_output=True, text=True, check=False)
        if r.stdout.strip():
            return Path(r.stdout.strip())
    return Path.home() / "Desktop"


def install() -> list[Path]:
    exe, args, env = _command()
    if WINDOWS:
        return _install_windows(exe, args, env)
    if MACOS:
        return _install_macos(exe, args, env)
    return _install_linux(exe, args, env)


def uninstall() -> list[Path]:
    removed = []
    for p in _paths():
        if p.is_dir() and not p.is_symlink():
            shutil.rmtree(p)
            removed.append(p)
        elif p.exists() or p.is_symlink():
            p.unlink()
            removed.append(p)
    return removed


def _paths() -> list[Path]:
    desktop = _desktop_dir()
    if WINDOWS:
        start = Path(os.environ.get("APPDATA", Path.home())) / "Microsoft/Windows/Start Menu/Programs"
        return [desktop / f"{APP_NAME}.lnk", start / f"{APP_NAME}.lnk"]
    if MACOS:
        return [desktop / f"{APP_NAME}.app", Path.home() / "Applications" / f"{APP_NAME}.app"]
    apps = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share")) / "applications"
    return [desktop / "trmm-web-relay.desktop", apps / "trmm-web-relay.desktop"]


def _install_linux(exe: str, args: list[str], env: dict) -> list[Path]:
    from shlex import quote

    cmd = " ".join(quote(a) for a in [exe, *args])
    if env:
        cmd = "env " + " ".join(f"{k}={quote(v)}" for k, v in env.items()) + " " + cmd
    entry = "\n".join([
        "[Desktop Entry]",
        "Type=Application",
        f"Name={APP_NAME}",
        "Comment=Weboberflächen in Kundennetzen über Tactical RMM öffnen",
        f"Exec={cmd}",
        f"Icon={ICON}",
        "Terminal=false",
        "Categories=Network;RemoteAccess;",
        "StartupNotify=false",
        "",
    ])
    written = []
    desktop, menu = _paths()
    menu.parent.mkdir(parents=True, exist_ok=True)
    for path in (desktop, menu):
        if not path.parent.exists():
            continue  # kein Desktop-Ordner
        path.write_text(entry)
        path.chmod(0o755)
        if shutil.which("gio"):
            # GNOME startet Desktop-Dateien erst, wenn sie als vertrauenswürdig markiert sind
            subprocess.run(["gio", "set", str(path), "metadata::trusted", "true"],
                           capture_output=True, check=False)
        written.append(path)
    return written


def _install_macos(exe: str, args: list[str], env: dict) -> list[Path]:
    from shlex import quote

    desktop_link, app = _paths()
    if app.exists():
        shutil.rmtree(app)
    (app / "Contents/MacOS").mkdir(parents=True)
    (app / "Contents/Resources").mkdir()
    exports = "".join(f"export {k}={quote(v)}\n" for k, v in env.items())
    launcher = app / "Contents/MacOS/trmm-web-relay"
    launcher.write_text(f"#!/bin/sh\n{exports}exec {quote(exe)} {' '.join(quote(a) for a in args)}\n")
    launcher.chmod(0o755)
    (app / "Contents/Info.plist").write_text(f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>CFBundleName</key><string>{APP_NAME}</string>
  <key>CFBundleIdentifier</key><string>org.bashclub.trmm-web-relay</string>
  <key>CFBundleExecutable</key><string>trmm-web-relay</string>
  <key>CFBundlePackageType</key><string>APPL</string>
  <key>LSUIElement</key><true/>
</dict></plist>
""")
    if desktop_link.is_symlink() or desktop_link.exists():
        desktop_link.unlink()
    desktop_link.symlink_to(app)
    return [app, desktop_link]


def _install_windows(exe: str, args: list[str], env: dict) -> list[Path]:
    written = []
    arguments = " ".join(args)
    if env:
        # Verknüpfungen kennen keine Umgebung: über cmd setzen (nur beim Start aus dem Repo)
        sets = " && ".join(f'set "{k}={v}"' for k, v in env.items())
        arguments = f'/c {sets} && start "" "{exe}" {arguments}'
        exe = os.environ.get("COMSPEC", "cmd.exe")
    for path in _paths():
        path.parent.mkdir(parents=True, exist_ok=True)
        ps = (
            "$s=(New-Object -ComObject WScript.Shell).CreateShortcut($env:WR_LNK);"
            "$s.TargetPath=$env:WR_EXE;$s.Arguments=$env:WR_ARGS;"
            "$s.WorkingDirectory=$env:USERPROFILE;$s.WindowStyle=7;$s.Save()"
        )
        subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps],
            env={**os.environ, "WR_LNK": str(path), "WR_EXE": exe, "WR_ARGS": arguments},
            check=True, capture_output=True, **quiet(),
        )
        written.append(path)
    return written
