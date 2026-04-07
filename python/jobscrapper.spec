# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['src/api.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('src/db/schema.sql', 'src/db'),
    ],
    hiddenimports=[
        'src.scrapers.registry_loader',
        'src.scrapers.helpers.browser_pool',
        'src.scrapers.adzuna',
        'src.scrapers.apec',
        'src.scrapers.cadremploi',
        'src.scrapers.francetravail',
        'src.scrapers.freework',
        'src.scrapers.glassdoor',
        'src.scrapers.hellowork',
        'src.scrapers.indeed',
        'src.scrapers.linkedin',
        'src.scrapers.monster',
        'src.scrapers.welcometothejungle',
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
