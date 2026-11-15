# SPDX-License-Identifier: GPL-3.0-or-later
"""Ein Terminalfenster mit einem Befehl des Clients öffnen (für SSH-Ziele).

Linux: Einstellung `terminal`, sonst xdg-terminal-exec, das Terminal des
Desktops, x-terminal-emulator und bekannte Terminals der Reihe nach.
macOS: Terminal.app. Windows: neues Konsolenfenster (unter Windows 11 das
eingestellte Standardterminal, meist Windows Terminal).
"""

import os
import shlex
import shutil
import subprocess
import sys
from functools import cache
from pathlib import Path

from trmmwebrelay.config import Config
from trmmwebrelay.platform import MACOS, PACKAGE_DIR, WINDOWS, detached, quiet

# Programm und die Argumente, nach denen der Befehl folgt
_LINUX = [
    ("xdg-terminal-exec", []),
    ("ptyxis", ["--new-window", "--"]),
    ("kgx", ["--"]),
    ("gnome-terminal", ["--"]),
    ("konsole", ["-e"]),
    ("xfce4-terminal", ["-x"]),
    ("mate-terminal", ["-x"]),
    ("x-terminal-emulator", ["-e"]),
    ("alacritty", ["-e"]),
    ("kitty", []),
    ("foot", []),
    ("wezterm", ["start", "--"]),
    ("xterm", ["-e"]),
]
# Terminal des Desktops zuerst (XDG_CURRENT_DESKTOP)
_DESKTOP = {"GNOME": "ptyxis kgx gnome-terminal", "KDE": "konsole", "XFCE": "xfce4-terminal", "MATE": "mate-terminal"}


@cache
def _client_env() -> dict:
    """PYTHONPATH, falls der Client aus dem Repo läuft (nicht installiert)."""
    clean = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    r = subprocess.run(
        [sys.executable, "-c", "import trmmwebrelay; print(trmmwebrelay.__file__)"],
        capture_output=True, text=True, check=False, env=clean, cwd=Path.home(), **quiet(),
    )
    if r.returncode != 0 or Path(r.stdout.strip()).parent.resolve() != PACKAGE_DIR.resolve():
        return {"PYTHONPATH": str(PACKAGE_DIR.parent)}
    return {}


def _python() -> str:
    exe = sys.executable
    if WINDOWS:
        # pythonw (Startsymbol) hat keine Konsole: python.exe für das Terminal
        p = Path(exe).with_name("python.exe")
        if p.exists():
            return str(p)
    return exe


def client_command(*args: str) -> list[str]:
    """Befehl, der `trmm-web-relay <args>` startet, unabhängig von PATH."""
    cmd = [_python(), "-m", "trmmwebrelay", *args]
    env = _client_env()
    if env and not WINDOWS:
        cmd = ["env", *(f"{k}={v}" for k, v in env.items()), *cmd]
    return cmd


def find_linux(cfg: Config) -> list[str]:
    if cfg.terminal.strip():
        return shlex.split(cfg.terminal)
    desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").upper()
    preferred = [n for key, names in _DESKTOP.items() if key in desktop for n in names.split()]
    order = sorted(_LINUX, key=lambda t: (t[0] != "xdg-terminal-exec", t[0] not in preferred))
    for name, args in order:
        if shutil.which(name):
            return [name, *args]
    raise RuntimeError("Kein Terminal gefunden (Einstellung „terminal“ setzen, z. B. \"konsole -e\")")


def launch(cfg: Config, cmd: list[str]) -> None:
    """cmd in einem neuen Terminalfenster starten."""
    if WINDOWS:
        env = {**os.environ, **_client_env()}
        if cfg.terminal.strip():
            subprocess.Popen([*shlex.split(cfg.terminal, posix=False), *cmd], env=env)
        else:
            subprocess.Popen(cmd, env=env, creationflags=subprocess.CREATE_NEW_CONSOLE)
        return
    if MACOS and not cfg.terminal.strip():
        line = shlex.join(cmd).replace("\\", "\\\\").replace('"', '\\"')
        subprocess.Popen(
            ["osascript", "-e", f'tell application "Terminal" to do script "{line}"',
             "-e", 'tell application "Terminal" to activate'],
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        return
    term = shlex.split(cfg.terminal) if MACOS else find_linux(cfg)
    subprocess.Popen([*term, *cmd], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL, **detached())
