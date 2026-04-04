"""
PyInstaller runtime hook — configure Playwright browser path.

Sur Mac : les browsers sont bundlés dans _MEIPASS/ms-playwright.
Sur Windows : Edge est détecté automatiquement dans browser.py.
"""

import os
import sys
from pathlib import Path

if getattr(sys, "frozen", False):
    bundle_dir = Path(sys._MEIPASS)  # type: ignore[attr-defined]
    browsers_path = bundle_dir / "ms-playwright"
    if browsers_path.exists():
        os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(browsers_path)
