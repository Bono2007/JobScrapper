# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from pathlib import Path

# Sur Mac en CI, Playwright installe Chromium dans ~/Library/Caches/ms-playwright
# On le bundle dans le binaire pour que l'app fonctionne sans installation supplémentaire.
# Sur Windows, Edge est utilisé directement (toujours présent sur Win10/11).
_playwright_browsers_datas = []
if sys.platform == "darwin":
    _ms_playwright = Path.home() / "Library" / "Caches" / "ms-playwright"
    if _ms_playwright.exists():
        _playwright_browsers_datas = [
            (str(_ms_playwright), "ms-playwright"),
        ]

a = Analysis(
    ['src/api.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('src/db/schema.sql', 'src/db'),
        *_playwright_browsers_datas,
    ],
    hiddenimports=[
        'src.scrapers.registry_loader',
        'src.scrapers.adzuna',
        'src.scrapers.apec',
        'src.scrapers.cadremploi',
        'src.scrapers.cadresonline',
        'src.scrapers.francetravail',
        'src.scrapers.glassdoor',
        'src.scrapers.hellowork',
        'src.scrapers.indeed',
        'src.scrapers.jobijoba',
        'src.scrapers.linkedin',
        'src.scrapers.malt',
        'src.scrapers.monster',
        'src.scrapers.welcometothejungle',
        'src.scrapers.wizbii',
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
    ],
    hookspath=[],
    runtime_hooks=['pyi_rthook_playwright.py'],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='api',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
)
