"""Deterministic rice counter. All areas are contour areas in pixel squared."""
import argparse
import csv
import json
import hashlib
from pathlib import Path

import cv2
import numpy as np


def analyze(image, threshold=127, min_area=30, roi=None, invert=False, blur=0):
    if image is None or image.dtype != np.uint8 or image.ndim != 3 or image.shape[2] != 3:
        raise ValueError("Expected a uint8 BGR image")
    if not 0 <= threshold <= 255 or min_area < 0:
        raise ValueError("Threshold must be 0..255 and minimum area nonnegative")
    if blur not in (0, 3, 5, 7):
        raise ValueError("Blur must be 0, 3, 5, or 7")
    height, width = image.shape[:2]
    x, y, w, h = roi if roi is not None else (0, 0, width, height)
    if x < 0 or y < 0 or w <= 0 or h <= 0 or x + w > width or y + h > height:
        raise ValueError("ROI must lie inside the image")
    gray = cv2.cvtColor(image[y:y+h, x:x+w], cv2.COLOR_BGR2GRAY)
    if blur:
        gray = cv2.GaussianBlur(gray, (blur, blur), 0)
    mode = cv2.THRESH_BINARY_INV if invert else cv2.THRESH_BINARY
    _, binary = cv2.threshold(gray, threshold, 255, mode)
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=lambda c: (cv2.boundingRect(c)[1], cv2.boundingRect(c)[0]))
    overlay = image.copy()
    mask = np.zeros((height, width), np.uint8)
    accepted = np.zeros((h, w), np.uint8)
    particles = []
    border_count = 0
    background_count = 0
    for contour in contours:
        area = cv2.contourArea(contour)
        if area < min_area or area <= 0:
            continue
        bx, by, bw, bh = cv2.boundingRect(contour)
        if bx == 0 or by == 0 or bx + bw == w or by + bh == h:
            border_count += 1
            continue
        # Rice candidates should not be branching texture or sparse bright rings.
        # These conservative shape checks are not a semantic rice classifier.
        hull_area = cv2.contourArea(cv2.convexHull(contour))
        perimeter = cv2.arcLength(contour, True)
        solidity = area / hull_area if hull_area else 0
        compactness = 4 * np.pi * area / perimeter ** 2 if perimeter else 0
        if solidity < 0.55 or compactness < 0.08:
            background_count += 1
            continue
        region = np.zeros((bh, bw), np.uint8)
        cv2.drawContours(region, [contour - [bx, by]], -1, 255, cv2.FILLED)
        foreground = cv2.countNonZero(cv2.bitwise_and(binary[by:by+bh, bx:bx+bw], region))
        if foreground / cv2.countNonZero(region) < 0.35:
            background_count += 1
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
            "background_excluded": background_count,
            "background_filter": {"min_solidity": 0.55, "min_compactness": 0.08, "min_foreground_fraction": 0.35},
            "roi": [x, y, w, h], "threshold": threshold,
            "min_area_px2": min_area, "invert": invert, "blur": blur}


def starting_threshold(image, blur=0, roi=None):
    """Otsu provides a starting value, not a guarantee of correct segmentation."""
    if roi is not None:
        x, y, w, h = roi
        image = image[y:y+h, x:x+w]
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    if blur:
        gray = cv2.GaussianBlur(gray, (blur, blur), 0)
    value, _ = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return int(value)


def photo_directory(directory, source):
    source = Path(source).resolve()
    suffix = hashlib.sha256(str(source).encode()).hexdigest()[:8]
    return Path(directory) / f"{source.stem}_{suffix}"


def save_photo(result, source, directory):
    """Preserve separate photo exports and rebuild a per-photo index."""
    destination = photo_directory(directory, source)
    save_result(result, source, destination)
    rows = []
    for path in sorted(Path(directory).glob("*/summary.json")):
        summary = json.loads(path.read_text())
        rows.append({"source": summary["source"], "count": len(summary["particles"]),
                     "border_excluded": summary["border_excluded"], "threshold": summary["threshold"],
                     "min_area_px2": summary["min_area_px2"], "blur": summary.get("blur", 0),
                     "unit": "px2", "calibrated": False, "output": str(path.parent.resolve())})
    with (Path(directory) / "photo_results.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return destination


def draw_dashboard(figure, axes, result, source):
    """Shared four-panel presentation for the application and PNG export."""
    from matplotlib.ticker import MaxNLocator
    for axis in axes:
        axis.clear()
    for axis, key, title in ((axes[0], "overlay", "Input image + ROI (drag to select)"),
                             (axes[1], "mask_numbered", "Numbered particle mask")):
        axis.imshow(cv2.cvtColor(result[key], cv2.COLOR_BGR2RGB))
        axis.set_title(title, loc="left")
        for particle in result["particles"]:
            axis.annotate(str(particle["id"]), (particle["cx_px"], particle["cy_px"]),
                          xytext=(0, 12), textcoords="offset points", ha="center",
                          fontsize=11, color="yellow", fontweight="bold",
                          bbox={"facecolor": "black", "alpha": 0.7, "edgecolor": "none"})
        axis.set(xlabel="X (px)", ylabel="Y (px)")
    areas = [p["area_px2"] for p in result["particles"]]
    if areas:
        axes[2].hist(areas, bins=min(10, len(areas)), color="#258b83", edgecolor="white")
    else:
        axes[2].text(0.5, 0.5, "No accepted particles", ha="center", transform=axes[2].transAxes)
    axes[2].set(title="Size distribution", xlabel="Contour area (px²)", ylabel="Particle count")
    axes[2].yaxis.set_major_locator(MaxNLocator(integer=True))
    axes[3].set_axis_off()
    visible = result["particles"][:12]
    axes[3].set_title(f"Particle results — showing {len(visible)} of {len(areas)}", loc="left")
    if visible:
        table = axes[3].table(cellText=[[p["id"], f"{p['area_px2']:,.1f}"] for p in visible],
                              colLabels=["Particle ID", "Area (px²)"], cellLoc="center",
                              bbox=[0.05, 0.08, 0.9, 0.82])
        table.auto_set_font_size(False)
        table.set_fontsize(11)
    else:
        axes[3].text(0.5, 0.5, "No accepted particles", ha="center", transform=axes[3].transAxes)
    axes[3].text(0.5, 0, "Complete measurements are saved in particles.csv", ha="center",
                 transform=axes[3].transAxes, fontsize=9)
    figure.suptitle("PARTICLE COUNTER & SIZE DISTRIBUTION ANALYZER\n"
                    f"Count: {len(areas)} | Border excluded: {result['border_excluded']} | "
                    f"Threshold: {result['threshold']} | Min area: {result['min_area_px2']:g} px² | "
                    f"Blur: {result.get('blur', 0)} | px² — UNCALIBRATED", fontsize=13)
    for text in list(figure.texts):
        if text is not figure._suptitle:
            text.remove()
    note = "Synthetic dataset montage — not a physical experiment. " if Path(source).name == "synthetic_montage.png" else ""
    figure.text(0.5, 0.06, f"Source: {Path(source).name}\n{note}Touching grains may merge; counts are unverified. Physical size is uncalibrated.",
                ha="center", fontsize=9, color="#8c3300")
    figure.text(0.5, 0.015, "Drag: ROI | +/-: threshold | A: auto threshold | [/]: min area | B: smoothing | I: invert | R: reset | S: save | Q: quit",
                ha="center", fontsize=10)
    figure.subplots_adjust(top=0.84, bottom=0.17, left=0.07, right=0.97, hspace=0.45, wspace=0.3)


def save_dashboard(result, source, destination):
    from matplotlib.figure import Figure
    figure = Figure(figsize=(14, 9))
    draw_dashboard(figure, figure.subplots(2, 2).ravel(), result, source)
    figure.savefig(destination, dpi=130)


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
    save_dashboard(result, source, directory / "dashboard.png")


def interactive(image, source, args):
    import matplotlib.pyplot as plt
    from matplotlib.widgets import RectangleSelector, Button
    # Reserve our shortcuts; Matplotlib otherwise opens its save dialog on 's'.
    for action in ("save", "quit", "xscale", "yscale"):
        plt.rcParams[f"keymap.{action}"] = []
    state = {"threshold": args.threshold, "roi": args.roi, "invert": args.invert,
             "min_area": args.min_area, "blur": getattr(args, "blur", 0)}
    settings_path = getattr(args, "photo_settings", None)
    photo_settings = json.loads(Path(settings_path).read_text()) if settings_path else {}
    figure, grid = plt.subplots(2, 2, figsize=(14, 9))
    figure.canvas.manager.set_window_title("Rice Particle Counter — Interactive System")
    axes = grid.ravel()
    current = {}

    def redraw():
        current["result"] = analyze(image, state["threshold"], state["min_area"], state["roi"], state["invert"], state["blur"])
        result = current["result"]
        draw_dashboard(figure, axes, result, source)
        figure.subplots_adjust(bottom=0.25)
        figure.canvas.draw_idle()

    def load_image(path):
        nonlocal image, source
        loaded = cv2.imread(str(path))
        if loaded is None:
            status.set_text(f"Cannot read: {Path(path).name}")
            figure.canvas.draw_idle()
            return
        image, source = loaded, Path(path)
        state["roi"] = None
        if getattr(args, "auto_threshold", False):
            state["threshold"] = starting_threshold(image, state["blur"])
        if Path(source).name in photo_settings:
            state["threshold"] = photo_settings[Path(source).name]
            state["min_area"] = round(image.shape[0] * image.shape[1] * 0.00004)
        selector.set_visible(False)
        status.set_text(f"Loaded: {source.name}")
        redraw()

    def open_image(event):
        from tkinter import Tk, filedialog
        root = Tk()
        root.withdraw()
        try:
            selected = filedialog.askopenfilename(title="Open rice image", initialdir=str(Path(source).parent),
                                                  filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp *.tif *.tiff"), ("All files", "*")])
        finally:
            root.destroy()
        if selected:
            load_image(selected)

    def browse(step):
        folder = Path(source).parent
        files = sorted(p for p in folder.iterdir() if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"))
        if files:
            index = files.index(Path(source)) if Path(source) in files else 0
            load_image(files[(index + step) % len(files)])

    def save():
        try:
            destination = save_photo(current["result"], source, args.output)
        except OSError as error:
            status.set_text(f"Save failed: {error}")
        else:
            status.set_text(f"Saved: {destination.name} | Index: photo_results.csv")
        figure.canvas.draw_idle()

    def reset():
        state["roi"] = None
        selector.set_visible(False)
        redraw()

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
        elif event.key == "a":
            state["threshold"] = starting_threshold(image, state["blur"], state["roi"])
        elif event.key in ("[", "]"):
            state["min_area"] = max(1, state["min_area"] * (0.8 if event.key == "[" else 1.25))
        elif event.key == "b":
            options = (0, 3, 5, 7)
            state["blur"] = options[(options.index(state["blur"]) + 1) % len(options)]
        elif event.key == "r":
            reset()
            return
        elif event.key == "s":
            save()
            return
        elif event.key == "o":
            open_image(event)
            return
        elif event.key in ("left", "right"):
            browse(-1 if event.key == "left" else 1)
            return
        elif event.key in ("q", "escape"):
            plt.close(figure)
            return
        else:
            return
        redraw()

    redraw()
    selector = RectangleSelector(axes[0], select, button=[1], minspanx=2, minspany=2, spancoords="pixels")
    buttons = []
    controls = [("Open image", open_image), ("Previous", lambda event: browse(-1)),
                ("Next", lambda event: browse(1)), ("Reset ROI", lambda event: reset()),
                ("Save results", lambda event: save())]
    for index, (label, callback) in enumerate(controls):
        button = Button(figure.add_axes([0.07 + index * 0.18, 0.13, 0.15, 0.045]), label)
        button.on_clicked(callback)
        buttons.append(button)
    status_axis = figure.add_axes([0.07, 0.19, 0.9, 0.025])
    status_axis.set_axis_off()
    status = status_axis.text(0, 0, "Ready | O: open | Left/Right: browse | S: save per photo (same photo replaces its previous export)", fontsize=9)
    figure.canvas.mpl_connect("key_press_event", key)
    plt.show()
    return selector


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path, nargs="?", default=Path(__file__).parent / "data/samples/synthetic_montage.png",
                        help="Image to analyze; defaults to the synthetic dataset demo")
    parser.add_argument("--threshold", type=int, default=127)
    parser.add_argument("--min-area", type=float, default=30)
    parser.add_argument("--blur", type=int, choices=(0, 3, 5, 7), default=0)
    parser.add_argument("--auto-threshold", action="store_true", help="Start each loaded image with Otsu threshold")
    parser.add_argument("--photo-settings", type=Path, help="JSON mapping photo filenames to starting thresholds")
    parser.add_argument("--roi", nargs=4, type=int, metavar=("X", "Y", "W", "H"))
    parser.add_argument("--invert", action="store_true", help="Dark particles on bright background")
    parser.add_argument("--headless", action="store_true", help="Save outputs without opening GUI")
    parser.add_argument("--output", type=Path, default=Path(__file__).parent / "outputs" / "latest")
    args = parser.parse_args()
    image = cv2.imread(str(args.image))
    if image is None:
        parser.error(f"Cannot read image: {args.image}")
    if args.photo_settings:
        settings = json.loads(args.photo_settings.read_text())
        if args.image.name in settings:
            args.threshold = settings[args.image.name]
            args.min_area = round(image.shape[0] * image.shape[1] * 0.00004)
    try:
        result = analyze(image, args.threshold, args.min_area, args.roi, args.invert, args.blur)
        if args.auto_threshold:
            args.threshold = starting_threshold(image, args.blur, args.roi)
            result = analyze(image, args.threshold, args.min_area, args.roi, args.invert, args.blur)
    except ValueError as error:
        parser.error(str(error))
    if args.headless:
        destination = save_photo(result, args.image, args.output)
        print(f"Count={len(result['particles'])}; border_excluded={result['border_excluded']}; output={destination.resolve()}")
    else:
        interactive(image, args.image, args)


if __name__ == "__main__":
    main()