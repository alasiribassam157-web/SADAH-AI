"""Expose the local platform through a free Cloudflare quick tunnel and save the links.

Visitors coming through the tunnel get the safe public experience: no developer page and
no code/system execution (the tunnel adds Cf-Connecting-IP, see dev_api.is_local).
Quick-tunnel URLs change on every launch; the permanent link is the Render deployment.
"""
import os
import re
import subprocess
import sys
import time
import urllib.request
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BIN = ROOT / "deploy" / "bin"
PORT = int(os.getenv("PORT", "8000"))
LOCAL = f"http://localhost:{PORT}"
CLOUD = "https://sadah-app.vercel.app"
CLOUDFLARED_URL = ("https://github.com/cloudflare/cloudflared/releases/latest/download/"
                   "cloudflared-windows-amd64.exe")


def wait_for_server(timeout: int = 90) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen(f"{LOCAL}/api/health", timeout=2)
            return True
        except OSError:
            time.sleep(1)
    return False


def desktop_dir() -> Path:
    home = Path(os.environ.get("USERPROFILE", Path.home()))
    for candidate in (home / "Desktop", home / "OneDrive" / "Desktop"):
        if candidate.is_dir():
            return candidate
    return ROOT


def save_links(public_url: str | None) -> None:
    lines = ["SADAH links", "=" * 40,
             f"Permanent (everyone, 24/7):  {CLOUD}",
             f"This PC:                     {LOCAL}",
             f"Developer (this PC only):    {LOCAL}/dev"]
    if public_url:
        lines.append(f"Temporary tunnel:            {public_url}   (changes every launch)")
    lines += ["", f"Updated: {time.strftime('%Y-%m-%d %H:%M:%S')}"]
    text = "\n".join(lines) + "\n"
    for folder in {ROOT, desktop_dir()}:
        (folder / "PERMANENT_LINK.txt").write_text(text, encoding="utf-8")
    print("\n" + text)


def _runs(exe: Path) -> bool:
    try:
        return subprocess.run([str(exe), "--version"], capture_output=True, timeout=15).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def cloudflare() -> tuple[subprocess.Popen, str] | None:
    exe = BIN / "cloudflared.exe"
    if not _runs(exe):
        print("Downloading cloudflared (one-time)...")
        BIN.mkdir(parents=True, exist_ok=True)
        part = exe.with_suffix(".part")
        try:
            # Download to a temp name so an interrupted download never leaves a broken exe.
            urllib.request.urlretrieve(CLOUDFLARED_URL, part)
            part.replace(exe)
        except OSError as exc:
            print(f"cloudflared download failed: {exc}")
            return None
        if not _runs(exe):
            print("cloudflared binary is not runnable.")
            return None
    proc = subprocess.Popen([str(exe), "tunnel", "--no-autoupdate", "--url", LOCAL],
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    regex, deadline = re.compile(r"https://[a-z0-9-]+\.trycloudflare\.com"), time.time() + 40
    while time.time() < deadline and proc.poll() is None:
        match = regex.search(proc.stdout.readline() or "")
        if match:
            return proc, match.group(0)
    proc.kill()
    return None


def main() -> int:
    print(f"Waiting for SADAH on {LOCAL} ...")
    if not wait_for_server():
        print("Server did not start. Check the 'SADAH Server' window for errors.")
        return 1
    tunnel = cloudflare()
    save_links(tunnel[1] if tunnel else None)
    webbrowser.open(f"{LOCAL}/dev")
    if not tunnel:
        print("No public tunnel available - local link only.")
        return 0
    print("Tunnel active. Press Ctrl+C to stop.")
    try:
        tunnel[0].wait()
    except KeyboardInterrupt:
        tunnel[0].terminate()
    return 0


if __name__ == "__main__":
    sys.exit(main())
