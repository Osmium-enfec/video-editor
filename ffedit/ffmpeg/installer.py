"""Runtime helper to ensure an ffmpeg binary is available.

Provides `get_ffmpeg_path()` and `ensure_ffmpeg_available()` to locate,
download or install ffmpeg into a local app directory when missing.
"""

import os
import sys
import shutil
import stat
import subprocess
import platform
import tempfile
from pathlib import Path
from urllib.request import urlopen, Request
from zipfile import ZipFile


def _app_ffmpeg_dir() -> str:
    # Use a user-writable folder to store bundled ffmpeg if needed
    d = os.environ.get("FFEDIT_FFMPEG_DIR")
    if d:
        return d
    return os.path.join(os.path.expanduser("~"), ".ffedit", "ffmpeg")


def _config_file() -> str:
    d = os.path.join(os.path.expanduser("~"), ".ffedit")
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, "config.json")


def save_ffmpeg_path(path: str) -> None:
    """Persist the ffmpeg path to the user config file."""
    import json
    cfg = {}
    cfg_path = _config_file()
    if os.path.exists(cfg_path):
        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
        except Exception:
            cfg = {}
    cfg["ffmpeg_path"] = path
    try:
        with open(cfg_path, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
    except Exception:
        pass


def load_ffmpeg_path() -> str | None:
    """Load persisted ffmpeg path from user config or return None."""
    import json
    cfg_path = _config_file()
    if not os.path.exists(cfg_path):
        return None
    try:
        with open(cfg_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        return cfg.get("ffmpeg_path")
    except Exception:
        return None


def _meipass_ffmpeg() -> str:
    # When packaged by PyInstaller, files can be in _MEIPASS
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        # Look for architecture-specific ffmpeg inside packaged ffmpeg folder
        arch = platform.machine().lower()
        is_windows = platform.system().lower() == "windows"
        candidates = []
        if is_windows:
            candidates = [f"ffmpeg-{arch}.exe", "ffmpeg.exe"]
        else:
            candidates = [f"ffmpeg-{arch}", f"ffmpeg-{arch.replace('aarch64','arm64')}", "ffmpeg", "ffmpeg.exe"]
        for name in candidates:
            p = os.path.join(meipass, "ffmpeg", name)
            if os.path.exists(p):
                return p
    return None


def get_ffmpeg_path(preferred_binary: str = "ffmpeg") -> str | None:
    """Return path to an ffmpeg binary or None if not found.

    Checks system PATH, environment override, packaged location, and
    local user ffmpeg directory.
    """
    # 1. Persisted config override
    cfg = load_ffmpeg_path()
    if cfg and os.path.exists(cfg):
        return cfg

    # 2. Environment override
    env = os.environ.get("FFEDIT_FFMPEG")
    if env and os.path.exists(env):
        return env

    # 2. System PATH
    sys_path = shutil.which(preferred_binary)
    if sys_path:
        return sys_path

    # 3. PyInstaller bundle
    meipass = _meipass_ffmpeg()
    if meipass:
        return meipass

    # 4. User install dir (support arch-specific names)
    usr = _app_ffmpeg_dir()
    arch = platform.machine().lower()
    candidates = []
    if platform.system().lower() == "windows":
        candidates = [f"ffmpeg-{arch}.exe", "ffmpeg.exe"]
    else:
        candidates = [f"ffmpeg-{arch}", f"ffmpeg-{arch.replace('aarch64','arm64')}", "ffmpeg", "ffmpeg.exe"]
    for name in candidates:
        p = os.path.join(usr, name)
        if os.path.exists(p):
            return p

    return None


def _download_url_to_file(url: str, dest: str) -> None:
    req = Request(url, headers={"User-Agent": "ffedit-installer/1.0"})
    with urlopen(req, timeout=30) as resp, open(dest, "wb") as out:
        out.write(resp.read())


def _make_executable(path: str) -> None:
    st = os.stat(path)
    os.chmod(path, st.st_mode | stat.S_IEXEC)


def _install_mac(install_dir: str) -> str | None:
    # Try brew first
    try:
        if shutil.which("brew"):
            subprocess.run(["brew", "install", "ffmpeg"], check=True)
            return shutil.which("ffmpeg")
    except Exception:
        pass

    # Fallback: download prebuilt binary from evermeet.cx
    url = "https://evermeet.cx/ffmpeg/ffmpeg"
    os.makedirs(install_dir, exist_ok=True)
    dest = os.path.join(install_dir, "ffmpeg")
    try:
        _download_url_to_file(url, dest)
        _make_executable(dest)
        return dest
    except Exception:
        return None


def _install_windows(install_dir: str) -> str | None:
    # Try winget
    try:
        if shutil.which("winget"):
            subprocess.run(["winget", "install", "--silent", "FFmpeg.FFmpeg"], check=True)
            # winget usually installs to PATH
            p = shutil.which("ffmpeg")
            if p:
                return p
    except Exception:
        pass

    # Try choco
    try:
        if shutil.which("choco"):
            subprocess.run(["choco", "install", "ffmpeg", "-y"], check=True)
            p = shutil.which("ffmpeg")
            if p:
                return p
    except Exception:
        pass

    # Fallback: download a zip from gyan.dev and extract
    url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    os.makedirs(install_dir, exist_ok=True)
    try:
        with tempfile.TemporaryDirectory() as td:
            zip_path = os.path.join(td, "ffmpeg.zip")
            _download_url_to_file(url, zip_path)
            with ZipFile(zip_path, "r") as z:
                # Extract ffmpeg.exe from the zip's bin/ folder
                for name in z.namelist():
                    if name.endswith("ffmpeg.exe"):
                        z.extract(name, td)
                        src = os.path.join(td, name)
                        dest = os.path.join(install_dir, "ffmpeg.exe")
                        os.replace(src, dest)
                        return dest
    except Exception:
        return None

    return None


def ensure_ffmpeg_available(allow_download: bool = True) -> str | None:
    """Ensure ffmpeg is available. Returns path or None.

    Will attempt system package managers, then download binaries into the
    user ffedit folder if necessary.
    """
    p = get_ffmpeg_path()
    if p:
        return p

    if not allow_download:
        return None

    install_dir = _app_ffmpeg_dir()
    os.makedirs(install_dir, exist_ok=True)

    system = platform.system().lower()
    if system == "darwin":
        p = _install_mac(install_dir)
    elif system == "windows":
        p = _install_windows(install_dir)
    else:
        # Try system package manager for linux
        try:
            if shutil.which("apt-get"):
                subprocess.run(["sudo", "apt-get", "update"], check=False)
                subprocess.run(["sudo", "apt-get", "install", "-y", "ffmpeg"], check=True)
                p = shutil.which("ffmpeg")
        except Exception:
            p = None

    if p:
        return p

    # Final attempt: look if we saved a binary earlier
    return get_ffmpeg_path()
