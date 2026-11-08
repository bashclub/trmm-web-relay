# SPDX-License-Identifier: GPL-3.0-or-later
"""Brave (oder ein anderer Chromium-Browser) mit eigenem Profil für Kundenzugriffe.

Das Profil schickt alles an den lokalen SOCKS-Verteiler; der lässt nur Ziele
aktiver Sitzungen durch. Darum darf dieses Profil Zertifikatsfehler
ignorieren, ohne dass das beim normalen Surfen gilt.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

from trmmwebrelay.config import STATE_DIR, Config
from trmmwebrelay.platform import WINDOWS, detached

PROFILE_DIR = STATE_DIR / "browser"

_CANDIDATES = [
    "brave-browser",
    "brave",
    "brave-browser-stable",
    "chromium",
    "chromium-browser",
    "google-chrome",
]
_MAC_CANDIDATES = [
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
]


def _windows_candidates() -> list[str]:
    out = []
    for base in (os.environ.get("LOCALAPPDATA"), os.environ.get("PROGRAMFILES"),
                 os.environ.get("PROGRAMFILES(X86)")):
        if not base:
            continue
        out += [
            os.path.join(base, r"BraveSoftware\Brave-Browser\Application\brave.exe"),
            os.path.join(base, r"Chromium\Application\chrome.exe"),
            os.path.join(base, r"Google\Chrome\Application\chrome.exe"),
            os.path.join(base, r"Microsoft\Edge\Application\msedge.exe"),
        ]
    return out


def find(cfg: Config) -> str | None:
    if cfg.browser:
        return cfg.browser
    if WINDOWS:
        return next((p for p in _windows_candidates() if Path(p).exists()), None)
    if sys.platform == "darwin":
        for path in _MAC_CANDIDATES:
            if Path(path).exists():
                return path
    for name in _CANDIDATES:
        path = shutil.which(name)
        if path:
            return path
    return None


def open_url(cfg: Config, url: str) -> None:
    exe = find(cfg)
    if not exe:
        raise RuntimeError("Kein Brave/Chromium gefunden (Einstellung „browser“ setzen)")
    PROFILE_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
    subprocess.Popen(
        [
            exe,
            f"--user-data-dir={PROFILE_DIR}",
            f"--proxy-server=socks5://127.0.0.1:{cfg.socks_port}",
            "--ignore-certificate-errors",
            "--no-first-run",
            "--no-default-browser-check",
            url,
        ],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        **detached(),
    )
