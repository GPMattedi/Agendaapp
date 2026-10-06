# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[('C:/Users/Mattedi/AppData/Local/Programs/Python/Python314/DLLs/_tkinter.pyd', '.'), ('C:/Users/Mattedi/AppData/Local/Programs/Python/Python314/DLLs/tcl86t.dll', '.'), ('C:/Users/Mattedi/AppData/Local/Programs/Python/Python314/DLLs/tk86t.dll', '.')],
    datas=[('assets/falling_from_heaven.png', 'assets'), ('C:/Users/Mattedi/AppData/Local/Programs/Python/Python314/tcl/tcl8.6', '_tcl_data'), ('C:/Users/Mattedi/AppData/Local/Programs/Python/Python314/tcl/tk8.6', '_tk_data')],
    hiddenimports=[],
    hookspath=['packaging_hooks'],
    hooksconfig={},
    runtime_hooks=['packaging_hooks/runtime_tk.py'],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Minha Agenda',
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
)
