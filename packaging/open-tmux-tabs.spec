# PyInstaller spec for the standalone Windows executable.
# Build from the repository root: pyinstaller packaging/open-tmux-tabs.spec
import os

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Textual and Rich import parts of themselves lazily; collect them fully.
hiddenimports = (
    collect_submodules("open_tmux_tabs")
    + collect_submodules("textual")
    + collect_submodules("rich")
)
datas = (
    collect_data_files(
        "open_tmux_tabs", includes=["app.tcss", "locales/*/LC_MESSAGES/*.mo"]
    )
    + collect_data_files("textual")
)

a = Analysis(
    [os.path.join(SPECPATH, "entry.py")],
    pathex=[os.path.join(SPECPATH, "..", "src")],
    hiddenimports=hiddenimports,
    datas=datas,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    name="open-tmux-tabs",
    console=True,
    upx=False,
)
