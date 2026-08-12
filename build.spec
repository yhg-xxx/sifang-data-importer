# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller 打包配置 - 四方数据导入工具"""

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('sheet_names.txt', '.'),
    ],
    hiddenimports=[
        'PySide6',
        'openpyxl',
        'pyodbc',
        'app',
        'app.config',
        'app.constants',
        'app.database',
        'app.date_utils',
        'app.excel_reader',
        'app.importer',
        'app.local_db',
        'app.logger',
        'app.validator',
        'ui',
        'ui.base_task_dialog',
        'ui.column_mapping_dialog',
        'ui.confirm_dialog',
        'ui.connection_dialog',
        'ui.import_dialog',
        'ui.main_window',
        'ui.sheet_directory_dialog',
        'ui.validate_dialog',
    ],
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
    name='四方数据导入工具',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=True,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
