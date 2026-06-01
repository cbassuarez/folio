"""Locate bundled themes."""
import os

THEMES_DIR = os.path.join(os.path.dirname(__file__), "themes")


def theme_css(name: str) -> str:
    path = os.path.join(THEMES_DIR, name, "theme.css")
    if not os.path.exists(path):
        avail = ", ".join(sorted(os.listdir(THEMES_DIR)))
        raise FileNotFoundError(f"theme '{name}' not found. Available: {avail}")
    return path
