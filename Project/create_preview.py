"""Export the dashboard layout shared with the interactive application."""
from pathlib import Path

import cv2

from particle_counter import analyze, save_dashboard


def main():
    root = Path(__file__).resolve().parent
    source = root / "data/samples/synthetic_montage.png"
    result = analyze(cv2.imread(str(source)))
    destination = root / "dokumentasi/current_output.png"
    destination.parent.mkdir(parents=True, exist_ok=True)
    save_dashboard(result, source, destination)
    print(destination)
    print("Detected:", len(result["particles"]), "| calibrated=False")


if __name__ == "__main__":
    main()