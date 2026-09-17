# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_submodules


hiddenimports = []
for package in (
    'sportorg',
    'serial',
    'sportident',
    'dateutil',
    'aiohttp',
    'jinja2',
    'docxtpl',
    'docx',
    'lxml',
    'pydantic',
    'requests',
    'urllib3',
    'orjson',
):
    hiddenimports += collect_submodules(package)

datas = [
    ('languages', 'languages'),
    ('templates', 'templates'),
    ('img', 'img'),
    ('sounds', 'sounds'),
    ('styles', 'styles'),
    ('configs', 'configs'),
    ('data', 'data'),
    ('LICENSE', '.'),
    ('changelog.md', '.'),
    ('changelog_ru.md', '.'),
]

a = Analysis(
    ['SportOrg.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['PySide2', 'PyQt5', 'PyQt6', 'tkinter', 'pywinusb'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='SportOrg',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    target_arch='arm64',
    codesign_identity=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name='SportOrg',
)
app = BUNDLE(
    coll,
    name='SportOrg.app',
    icon=None,
    bundle_identifier='ru.sportorg.tourism',
    info_plist={
        'CFBundleName': 'SportOrg Tourism',
        'CFBundleDisplayName': 'SportOrg Tourism',
        'CFBundleVersion': '1.7.1',
        'CFBundleShortVersionString': '1.7.1',
        'NSHighResolutionCapable': True,
    },
)
