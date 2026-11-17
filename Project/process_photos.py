"""Analyze a photo folder, preserving originals and recording unverified counts."""
import argparse
import json
from pathlib import Path

import cv2

from particle_counter import analyze, save_photo, starting_threshold


def main():
    root = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path)
    parser.add_argument("--output", type=Path, default=root / "outputs/manual_photos")
    parser.add_argument("--settings", type=Path, help="JSON mapping file names to reviewed starting thresholds")
    args = parser.parse_args()
    settings = json.loads(args.settings.read_text()) if args.settings else {}
    files = sorted(p for p in args.folder.iterdir() if p.suffix.lower() in (".jpg", ".jpeg", ".png"))
    if not files:
        parser.error("No supported images found")
    report = []
    for path in files:
        image = cv2.imread(str(path))
        if image is None:
            parser.error(f"Cannot read {path}")
        # Scale the noise-area cutoff with image pixel count; this is a development setting.
        min_area = round(image.shape[0] * image.shape[1] * 0.00004)
        threshold = settings.get(path.name, starting_threshold(image, 5))
        result = analyze(image, threshold, min_area, blur=5)
        destination = save_photo(result, path, args.output)
        sensitivity = {str(t): len(analyze(image, t, min_area, blur=5)["particles"])
                       for t in (max(0, threshold-10), threshold, min(255, threshold+10))}
        report.append({"source": str(path.resolve()), "shape": list(image.shape),
                       "threshold": threshold, "blur": 5, "min_area_px2": min_area,
                       "threshold_method": "reviewed starting setting" if path.name in settings else "Otsu starting setting",
                       "detected_objects": len(result["particles"]), "border_excluded": result["border_excluded"],
                       "threshold_sensitivity": sensitivity, "manual_reference_count": None,
                       "accuracy_verified": False, "output": str(destination.resolve()),
                       "limitation": "Touching grains may merge; noise may be detected. No physical calibration."})
        print(path.name, "threshold=", threshold, "detected objects=", len(result["particles"]), flush=True)
    (args.output / "photo_review.json").write_text(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()