"""Deterministic rice counter. All areas are contour areas in pixel squared."""
import argparse
import csv
import json
from pathlib import Path

import cv2
import numpy as np


def analyze(image, threshold=127, min_area=30, roi=None, invert=False):
    if image is None or image.dtype != np.uint8 or image.ndim != 3 or image.shape[2] != 3:
        raise ValueError("Expected a uint8 BGR image")
    if not 0 <= threshold <= 255 or min_area < 0:
        raise ValueError("Threshold must be 0..255 and minimum area nonnegative")
    height, width = image.shape[:2]
    x, y, w, h = roi if roi is not None else (0, 0, width, height)
    if x < 0 or y < 0 or w <= 0 or h <= 0 or x + w > width or y + h > height:
        raise ValueError("ROI must lie inside the image")
    gray = cv2.cvtColor(image[y:y+h, x:x+w], cv2.COLOR_BGR2GRAY)
    mode = cv2.THRESH_BINARY_INV if invert else cv2.THRESH_BINARY
    _, binary = cv2.threshold(gray, threshold, 255, mode)
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=lambda c: (cv2.boundingRect(c)[1], cv2.boundingRect(c)[0]))
    overlay = image.copy()
    mask = np.zeros((height, width), np.uint8)
    accepted = np.zeros((h, w), np.uint8)
    particles = []
    border_count = 0
    for contour in contours:
        area = cv2.contourArea(contour)
        if area < min_area or area <= 0:
            continue
        bx, by, bw, bh = cv2.boundingRect(contour)
        if bx == 0 or by == 0 or bx + bw == w or by + bh == h:
            border_count += 1
            continue
        moments = cv2.moments(contour)
        cx = x + moments["m10"] / moments["m00"]
        cy = y + moments["m01"] / moments["m00"]
        identifier = len(particles) + 1
        particles.append({"id": identifier, "area_px2": area, "cx_px": cx, "cy_px": cy})
        cv2.drawContours(accepted, [contour], -1, 255, cv2.FILLED)
        shifted = contour + np.array([[[x, y]]], dtype=contour.dtype)
        cv2.drawContours(overlay, [shifted], -1, (0, 255, 0), 1)
        cv2.putText(overlay, str(identifier), (round(cx), round(cy)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1, cv2.LINE_AA)
    mask[y:y+h, x:x+w] = accepted
    mask_numbered = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
    for particle in particles:
        cv2.putText(mask_numbered, str(particle["id"]),
                    (round(particle["cx_px"]), round(particle["cy_px"])),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1, cv2.LINE_AA)
    cv2.rectangle(overlay, (x, y), (x+w-1, y+h-1), (255, 160, 0), 1)
    return {"particles": particles, "overlay": overlay, "mask": mask, "mask_numbered": mask_numbered,
            "binary": binary, "border_excluded": border_count,
            "roi": [x, y, w, h], "threshold": threshold,
            "min_area_px2": min_area, "invert": invert}


def save_result(result, source, directory):
    from matplotlib.figure import Figure
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    for name in ("overlay", "mask", "mask_numbered", "binary"):
        if not cv2.imwrite(str(directory / f"{name}.png"), result[name]):
            raise OSError(f"Could not save {name}")
    with (directory / "particles.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["id", "area_px2", "cx_px", "cy_px"])
        writer.writeheader()
        writer.writerows(result["particles"])
    metadata = {k: v for k, v in result.items() if k not in ("overlay", "mask", "mask_numbered", "binary")}
    metadata.update(source=str(Path(source).resolve()), unit="px2", calibrated=False,
                    area_definition="external contour area; holes not subtracted")
    (directory / "summary.json").write_text(json.dumps(metadata, indent=2))
    figure = Figure(figsize=(7, 4))
    axis = figure.subplots()
    areas = [p["area_px2"] for p in result["particles"]]
    if areas:
        axis.hist(areas, bins=min(10, len(areas)), edgecolor="black")
    else:
        axis.text(0.5, 0.5, "No accepted particles", ha="center", transform=axis.transAxes)
    axis.set(xlabel="Contour area (px²)", ylabel="Particle count", title="Size distribution — uncalibrated")
    figure.tight_layout()
    figure.savefig(directory / "histogram.png")


def interactive(image, source, args):
    import matplotlib.pyplot as plt
    from matplotlib.widgets import RectangleSelector
    # Reserve our shortcuts; Matplotlib otherwise opens its save dialog on 's'.
    for action in ("save", "quit", "xscale", "yscale"):
        plt.rcParams[f"keymap.{action}"] = []
    state = {"threshold": args.threshold, "roi": args.roi, "invert": args.invert}
    figure, axes = plt.subplots(1, 3, figsize=(14, 5))
    current = {}

    def redraw():
        current["result"] = analyze(image, state["threshold"], args.min_area, state["roi"], state["invert"])
        result = current["result"]
        for axis in axes:
            axis.clear()
        axes[0].imshow(cv2.cvtColor(result["overlay"], cv2.COLOR_BGR2RGB))
        axes[0].set_title("Drag ROI here | full-image coordinates")
        axes[1].imshow(cv2.cvtColor(result["mask_numbered"], cv2.COLOR_BGR2RGB))
        axes[1].set_title("Numbered accepted particle mask")
        areas = [p["area_px2"] for p in result["particles"]]
        if areas:
            axes[2].hist(areas, bins=min(10, len(areas)), edgecolor="black")
        axes[2].set(xlabel="Contour area (px²)", ylabel="Count", title="Uncalibrated size distribution")
        figure.suptitle(f"Count: {len(areas)} | Border excluded: {result['border_excluded']} | "
                       f"Threshold: {state['threshold']} | +/-: threshold | i: invert | r: reset ROI | s: save | q: quit")
        figure.canvas.draw_idle()

    def select(start, end):
        if any(v is None for v in (start.xdata, start.ydata, end.xdata, end.ydata)):
            return
        height, width = image.shape[:2]
        x1, x2 = sorted((max(0, min(width, round(start.xdata))), max(0, min(width, round(end.xdata)))))
        y1, y2 = sorted((max(0, min(height, round(start.ydata))), max(0, min(height, round(end.ydata)))))
        if x2 > x1 and y2 > y1:
            state["roi"] = (x1, y1, x2-x1, y2-y1)
            redraw()

    def key(event):
        if event.key in ("+", "=", "up"):
            state["threshold"] = min(255, state["threshold"] + 5)
        elif event.key in ("-", "down"):
            state["threshold"] = max(0, state["threshold"] - 5)
        elif event.key == "i":
            state["invert"] = not state["invert"]
        elif event.key == "r":
            state["roi"] = None
        elif event.key == "s":
            save_result(current["result"], source, args.output)
            print(f"Saved to {Path(args.output).resolve()}")
            return
        elif event.key in ("q", "escape"):
            plt.close(figure)
            return
        else:
            return
        redraw()

    redraw()
    selector = RectangleSelector(axes[0], select, button=[1], minspanx=2, minspany=2, spancoords="pixels")
    figure.canvas.mpl_connect("key_press_event", key)
    plt.show()
    return selector


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path)
    parser.add_argument("--threshold", type=int, default=127)
    parser.add_argument("--min-area", type=float, default=30)
    parser.add_argument("--roi", nargs=4, type=int, metavar=("X", "Y", "W", "H"))
    parser.add_argument("--invert", action="store_true", help="Dark particles on bright background")
    parser.add_argument("--headless", action="store_true", help="Save outputs without opening GUI")
    parser.add_argument("--output", type=Path, default=Path(__file__).parent / "outputs" / "latest")
    args = parser.parse_args()
    image = cv2.imread(str(args.image))
    if image is None:
        parser.error(f"Cannot read image: {args.image}")
    try:
        result = analyze(image, args.threshold, args.min_area, args.roi, args.invert)
    except ValueError as error:
        parser.error(str(error))
    if args.headless:
        save_result(result, args.image, args.output)
        print(f"Count={len(result['particles'])}; border_excluded={result['border_excluded']}; output={args.output.resolve()}")
    else:
        interactive(image, args.image, args)


if __name__ == "__main__":
    main()