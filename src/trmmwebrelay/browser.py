# SPDX-License-Identifier: GPL-3.0-or-later
"""Brave (oder ein anderer Chromium-Browser) mit eigenem Profil für Kundenzugriffe.

Das Profil schickt alles an den lokalen SOCKS-Verteiler. Der lässt Ziele
aktiver Sitzungen durch den Tunnel und wenige freigegebene Hosts direkt ins
Internet (Erweiterungen, Passwortmanager); alles andere lehnt er ab. So können
fremde Webseiten in diesem Profil keine Anfragen in Kundennetze schicken.
Zertifikate prüft das Profil wie ein normaler Browser.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

from trmmwebrelay.config import STATE_DIR, Config
from trmmwebrelay.platform import WINDOWS, detached

PROFILE_DIR = STATE_DIR / "browser"

# Web Store und Download/Update von Erweiterungen (Chrome, Brave, Edge).
# Erweiterungen sind signiert, darum hier auch Port 80.
STORE_HOSTS = (
    "chromewebstore.google.com",
    "chrome.google.com",
    "clients2.google.com",
    "clients2.googleusercontent.com",
    "update.googleapis.com",
    "gvt1.com",
    "lh3.googleusercontent.com",
    "www.gstatic.com",
    "ssl.gstatic.com",
    "fonts.gstatic.com",
    "fonts.googleapis.com",
    "extensionupdater.brave.com",
    "crxdownload.brave.com",
    "microsoftedge.microsoft.com",
    "edge.microsoft.com",
)


def _host_matches(host: str, entry: str) -> bool:
    entry = entry.lower().strip().removeprefix("*.").rstrip(".")
    return bool(entry) and (host == entry or host.endswith("." + entry))


def direct_allowed(cfg: Config, host: str, port: int) -> bool:
    """True, wenn das Profil host:port direkt (ohne Tunnel) erreichen darf."""
    host = host.lower().rstrip(".")
    if cfg.extension_store and port in (80, 443):
        if any(_host_matches(host, e) for e in STORE_HOSTS):
            return True
    for raw in cfg.direct_hosts:
        entry, sep, p = raw.strip().rpartition(":")
        if not (sep and p.isdigit() and entry):
            entry, p = raw.strip(), "443"
        if int(p) == port and _host_matches(host, entry.strip("[]")):
            return True
    return False

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
            "--no-first-run",
            "--no-default-browser-check",
            *(["--ignore-certificate-errors"] if cfg.ignore_cert_errors else []),
            url,
        ],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        **detached(),
    )
