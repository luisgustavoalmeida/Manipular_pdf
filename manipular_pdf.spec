# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec — Manipulador PDF (Windows).

Gerar executável:
  build_exe.bat
  ou: pyinstaller manipular_pdf.spec
"""

from pathlib import Path

from PyInstaller.utils.hooks import collect_all

ROOT = Path(SPECPATH)

block_cipher = None

ctk_datas, ctk_binaries, ctk_hiddenimports = collect_all("customtkinter")
fitz_datas, fitz_binaries, fitz_hiddenimports = collect_all("fitz")

icon_ctk = None
for candidato in (
    ROOT / ".venv" / "Lib" / "site-packages" / "customtkinter" / "assets" / "icons" / "CustomTkinter_icon_Windows.ico",
    ROOT / "venv" / "Lib" / "site-packages" / "customtkinter" / "assets" / "icons" / "CustomTkinter_icon_Windows.ico",
):
    if candidato.is_file():
        icon_ctk = str(candidato)
        break

hiddenimports = [
    "recursos",
    "interface_grafica",
    "interface_grafica.app",
    "interface_grafica.sobre",
    "interface_grafica.tema",
    "interface_grafica.componentes",
    "interface_grafica.paineis",
    "interface_grafica.operacao_ativa",
    "deep_translator",
    "deep_translator.google",
    "bs4",
    "requests",
    "darkdetect",
] + ctk_hiddenimports + fitz_hiddenimports

a = Analysis(
    ["main.py"],
    pathex=[str(ROOT)],
    binaries=ctk_binaries + fitz_binaries,
    datas=[("sobre.json", ".")] + ctk_datas + fitz_datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="ManipuladorPDF",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_ctk,
)
