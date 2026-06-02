# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

block_cipher = None

project_dir = Path.cwd()
migrations_dir = project_dir / "migrations"

datas = []
if migrations_dir.exists():
    datas.append((str(migrations_dir), "migrations"))

hiddenimports = [
    "ui",
    "ui.main_window",
    "ui.secretary_frame",
    "ui.schedule_frame",
    "ui.leave_frame",
    "ui.holiday_frame",
    "ui.calendar_schedule_frame",
    "ui.ui_data_helpers",
    "database",
    "migration_runner",
    "duplicate_cleanup_tool",
    "scheduler_service",
    "excel_service",
    "openpyxl",
]

a = Analysis(
    ["main.py"],
    pathex=[str(project_dir)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="scheduler_app",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
)