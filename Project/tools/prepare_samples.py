"""Extract 10 original images per variety and build an explicitly synthetic montage."""
import json
from pathlib import Path
from zipfile import ZipFile

import cv2
import numpy as np

from particle_counter import analyze, save_result


def main():
    root = Path(__file__).resolve().parents[1]
    destination = root / "data" / "samples"
    destination.mkdir(parents=True, exist_ok=True)
    with ZipFile(root / "data" / "raw" / "rice-images-dataset.zip") as archive:
        names = archive.namelist()
        groups = sorted({name.split("/")[0] for name in names if name.lower().endswith(".jpg")})
        selected = []
        for group in groups:
            members = sorted(name for name in names if name.startswith(group + "/") and name.lower().endswith(".jpg"))[:10]
            for name in members:
                path = destination / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(archive.read(name))
                selected.append(name)
        citations = []
        for name in names:
            if name.lower().endswith(".txt"):
                path = destination / Path(name).name
                path.write_bytes(archive.read(name))
                citations.append(path.name)
    checks = []
    for name in selected:
        image = cv2.imread(str(destination / name))
        result = analyze(image)
        checks.append({"file": name, "shape": list(image.shape), "detected": len(result["particles"]),
                       "border_excluded": result["border_excluded"]})
    # No resizing: each original image is placed in a separated cell.
    montage_sources = [next(name for name in selected if name.startswith(group + "/")) for group in groups]
    images = [cv2.imread(str(destination / name)) for name in montage_sources]
    cell_h = max(image.shape[0] for image in images) + 20
    cell_w = max(image.shape[1] for image in images) + 20
    montage = np.zeros((cell_h, cell_w * len(images), 3), np.uint8)
    for index, image in enumerate(images):
        h, w = image.shape[:2]
        montage[10:10+h, index*cell_w+10:index*cell_w+10+w] = image
    montage_path = destination / "synthetic_montage.png"
    cv2.imwrite(str(montage_path), montage)
    result = analyze(montage)
    save_result(result, montage_path, root / "outputs" / "synthetic_montage")
    report = {"source": "https://www.kaggle.com/datasets/mbsoroush/rice-images-dataset",
              "selected_originals": selected, "citation_files": citations,
              "single_image_checks": checks, "threshold": 127, "min_area_px2": 30,
              "synthetic_montage": {"sources": montage_sources, "expected_count": len(images),
                                    "detected_count": len(result["particles"]), "resized": False},
              "limitation": "Synthetic composition, not physical validation; areas uncalibrated in px2."}
    (destination / "manifest.json").write_text(json.dumps(report, indent=2))
    print(f"Selected {len(selected)} original images from {len(groups)} varieties")
    print(f"Single-image count=1: {sum(check['detected'] == 1 for check in checks)}/{len(checks)}")
    print(f"Synthetic montage expected={len(images)} detected={len(result['particles'])}")


if __name__ == "__main__":
    main()