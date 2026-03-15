"""
Cross-platform build script for Inventory Manager.

Usage:
    python build.py            Build for the current platform
    python build.py --clean    Clean build artifacts before building

Requirements:
    pip install pyinstaller
"""

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
SPEC_FILE = ROOT / "InventoryManager.spec"
DIST_DIR = ROOT / "dist"
BUILD_DIR = ROOT / "build"


def clean():
    """Remove previous build artifacts."""
    for d in (DIST_DIR, BUILD_DIR):
        if d.exists():
            shutil.rmtree(d)
            print(f"Removed {d}")


def build():
    """Run PyInstaller with the spec file."""
    # Check pyinstaller is available
    try:
        subprocess.run(
            [sys.executable, "-m", "PyInstaller", "--version"],
            capture_output=True, check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: PyInstaller is not installed.")
        print("Run:  pip install pyinstaller")
        sys.exit(1)

    # Check spec file exists
    if not SPEC_FILE.exists():
        print(f"Error: {SPEC_FILE} not found.")
        sys.exit(1)

    # Check icon exists
    if sys.platform == "win32":
        icon = ROOT / "assets" / "icon.ico"
    elif sys.platform == "darwin":
        icon = ROOT / "assets" / "icon.icns"
    else:
        icon = ROOT / "assets" / "icon.png"

    if not icon.exists():
        print(f"Warning: Icon file {icon} not found. Building without icon.")

    print(f"Building for {sys.platform}...")
    print(f"Spec file: {SPEC_FILE}")
    print()

    result = subprocess.run(
        [sys.executable, "-m", "PyInstaller", str(SPEC_FILE), "--noconfirm"],
        cwd=str(ROOT),
    )

    if result.returncode != 0:
        print("\nBuild failed.")
        sys.exit(1)

    # Report output
    print()
    print("Build complete!")

    if sys.platform == "win32":
        output = DIST_DIR / "InventoryManager.exe"
    elif sys.platform == "darwin":
        output = DIST_DIR / "InventoryManager.app"
    else:
        output = DIST_DIR / "InventoryManager"

    if output.exists():
        if output.is_file():
            size_mb = output.stat().st_size / (1024 * 1024)
            print(f"Output: {output}  ({size_mb:.1f} MB)")
        else:
            print(f"Output: {output}")
    else:
        print(f"Expected output at {output}")


def main():
    if "--clean" in sys.argv:
        clean()

    build()


if __name__ == "__main__":
    main()
