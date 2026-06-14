from setuptools import setup

APP = ["tetris.py"]
DATA_FILES = []

OPTIONS = {
    "argv_emulation": False,
    "packages": ["pygame"],
    "includes": ["pygame"],
    "excludes": [
        "tkinter",
        "numpy",
        "PIL",
        "scipy",
        "matplotlib",
    ],
    "iconfile": None,
    "resources": ["sounds"],
    "plist": {
        "CFBundleName": "Tetris",
        "CFBundleDisplayName": "Tetris",
        "CFBundleIdentifier": "com.tetris.game",
        "CFBundleVersion": "1.0.0",
        "LSMinimumSystemVersion": "10.13",
        "NSHighResolutionCapable": True,
    },
}

setup(
    name="Tetris",
    app=APP,
    data_files=DATA_FILES,
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)
