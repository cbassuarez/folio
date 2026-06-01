"""Markdown/HTML -> PDF via pandoc + headless Chrome."""
from __future__ import annotations
import os
import shutil
import subprocess

_CHROME_CANDIDATES = [
    os.environ.get("FOLIO_CHROME", ""),
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    shutil.which("google-chrome") or "",
    shutil.which("chromium") or "",
    shutil.which("chrome") or "",
]


def chrome_bin() -> str:
    for c in _CHROME_CANDIDATES:
        if c and os.path.exists(c):
            return c
    raise RuntimeError(
        "Google Chrome / Chromium not found. Install Chrome or set "
        "FOLIO_CHROME=/path/to/chrome.")


def require_pandoc():
    if not shutil.which("pandoc"):
        raise RuntimeError("pandoc not found on PATH. Install pandoc (brew install pandoc).")


def html_to_pdf(html_path: str, out_pdf: str):
    subprocess.run(
        [chrome_bin(), "--headless", "--disable-gpu", "--no-pdf-header-footer",
         f"--print-to-pdf={out_pdf}", "--print-to-pdf-no-header",
         "--virtual-time-budget=10000", f"file://{os.path.abspath(html_path)}"],
        check=True, capture_output=True)


def md_to_pdf(md_path: str, out_pdf: str, css_paths: list[str],
              resource_paths: list[str], work_dir: str):
    """Render a markdown file to PDF: pandoc -> standalone HTML -> Chrome."""
    require_pandoc()
    os.makedirs(work_dir, exist_ok=True)
    html = os.path.join(work_dir, os.path.basename(md_path).replace(".md", ".html"))
    cmd = ["pandoc", md_path, "--standalone", "--embed-resources",
           "--resource-path=" + ":".join(resource_paths)]
    for c in css_paths:
        cmd.append(f"--css={c}")
    cmd += ["-o", html]
    subprocess.run(cmd, check=True)
    html_to_pdf(html, out_pdf)
