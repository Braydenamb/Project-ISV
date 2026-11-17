"""Launch the interactive application with the group's real photographs."""
from pathlib import Path
import subprocess
import sys


def main():
    root = Path(__file__).resolve().parent
    photos = sorted((root.parent / "foto").glob("*.jpeg"))
    if not photos:
        raise SystemExit(f"No JPEG photos found in {root.parent / 'foto'}")
    subprocess.run([sys.executable, str(root / "particle_counter.py"), str(photos[0]),
                    "--photo-settings", str(root / "dokumentasi/photo_settings.json"),
                    "--blur", "5", "--output", str(root / "outputs/manual_photos")], check=True)


if __name__ == "__main__":
    main()