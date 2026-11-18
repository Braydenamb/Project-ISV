import tempfile
import unittest
import csv
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backend_bases import KeyEvent, MouseEvent

import cv2
import numpy as np

from particle_counter import analyze, save_result, interactive, draw_dashboard, photo_directory, save_photo, starting_threshold


class CounterTests(unittest.TestCase):
    def setUp(self):
        self.image = np.zeros((120, 180, 3), np.uint8)
        cv2.rectangle(self.image, (10, 10), (30, 30), (255, 255, 255), -1)
        cv2.rectangle(self.image, (70, 50), (100, 80), (255, 255, 255), -1)

    def test_count_and_contour_area(self):
        result = analyze(self.image)
        self.assertEqual([p["area_px2"] for p in result["particles"]], [400, 900])

    def test_rejects_branching_background_and_sparse_rings(self):
        image = np.zeros((240, 400, 3), np.uint8)
        cv2.ellipse(image, (45, 60), (20, 7), 30, 0, 360, (255, 255, 255), -1)
        # Connected bright floor texture with long branches.
        cv2.line(image, (110, 30), (110, 190), (255, 255, 255), 3)
        for y in range(40, 190, 20):
            cv2.line(image, (110, y), (180, y), (255, 255, 255), 3)
        # RETR_EXTERNAL alone would incorrectly fill/count this bright ring.
        cv2.circle(image, (300, 100), 45, (255, 255, 255), 2)
        for invert in (False, True):
            result = analyze(255-image if invert else image, min_area=30, invert=invert)
            self.assertEqual(len(result["particles"]), 1)
            self.assertEqual(result["background_excluded"], 2)
            self.assertEqual(result["mask"][100, 300], 0)
            self.assertEqual(result["mask"][100, 110], 0)
            self.assertEqual(result["mask"][60, 45], 255)

    def test_shape_filter_retains_rotated_isolated_grains_and_roi(self):
        image = np.zeros((220, 300, 3), np.uint8)
        for center, axes, angle in (((50, 60), (20, 7), 0), ((140, 60), (22, 8), 45),
                                   ((230, 60), (20, 8), 90), ((140, 150), (12, 9), 135)):
            cv2.ellipse(image, center, axes, angle, 0, 360, (255, 255, 255), -1)
        for blur in (0, 3, 5, 7):
            result = analyze(image, blur=blur)
            self.assertEqual(len(result["particles"]), 4)
            self.assertEqual(result["background_excluded"], 0)
        result = analyze(image, roi=(100, 110, 80, 80))
        self.assertEqual(len(result["particles"]), 1)
        self.assertAlmostEqual(result["particles"][0]["cx_px"], 140, delta=1)

    def test_empty_and_threshold(self):
        self.assertEqual(len(analyze(np.zeros_like(self.image))["particles"]), 0)
        self.assertEqual(len(analyze(self.image, threshold=255)["particles"]), 0)

    def test_roi_and_global_centroid(self):
        result = analyze(self.image, roi=(60, 40, 60, 60))
        self.assertEqual(len(result["particles"]), 1)
        self.assertEqual(result["particles"][0]["cx_px"], 85)
        self.assertEqual(result["particles"][0]["cy_px"], 65)

    def test_border_exclusion(self):
        result = analyze(self.image, roi=(10, 10, 100, 80))
        self.assertEqual(result["border_excluded"], 1)
        self.assertEqual(len(result["particles"]), 1)

    def test_noise_filter_and_inversion(self):
        self.assertEqual(len(analyze(self.image, min_area=500)["particles"]), 1)
        self.assertEqual(len(analyze(255-self.image, invert=True)["particles"]), 2)

    def test_invalid_parameters(self):
        for params in ({"threshold": -1}, {"min_area": -1}, {"roi": (0, 0, 0, 5)}, {"roi": (0, 0, 200, 200)}):
            with self.assertRaises(ValueError):
                analyze(self.image, **params)

    def test_export_including_empty(self):
        with tempfile.TemporaryDirectory() as directory:
            for image in (self.image, np.zeros_like(self.image)):
                save_result(analyze(image), "synthetic.png", directory)
                for filename in ("overlay.png", "mask.png", "mask_numbered.png", "binary.png", "particles.csv", "summary.json", "histogram.png", "dashboard.png"):
                    self.assertTrue((Path(directory) / filename).is_file())
                summary = json.loads((Path(directory) / "summary.json").read_text())
                with (Path(directory) / "particles.csv").open() as stream:
                    rows = list(csv.DictReader(stream))
                self.assertEqual(len(rows), len(summary["particles"]))
                self.assertFalse(summary["calibrated"])
                self.assertEqual(summary["unit"], "px2")

    def test_numbered_mask_preserves_binary_mask(self):
        result = analyze(self.image)
        self.assertEqual(set(np.unique(result["mask"])), {0, 255})
        self.assertEqual(result["mask_numbered"].shape, self.image.shape)
        red = result["mask_numbered"][:, :, 2] > result["mask_numbered"][:, :, 1]
        self.assertTrue(np.any(red))
        np.testing.assert_array_equal(self.image[15, 15], [255, 255, 255])

    def test_interactive_callbacks(self):
        with tempfile.TemporaryDirectory() as directory, matplotlib.rc_context():
            args = SimpleNamespace(threshold=127, min_area=30, roi=None, invert=False, output=Path(directory))

            def exercise():
                figure = plt.gcf()
                figure.canvas.draw()
                self.assertEqual(len(figure.axes), 10)
                self.assertEqual(len(figure.axes[3].tables), 1)
                axis = figure.axes[0]
                start = axis.transData.transform((5, 5))
                end = axis.transData.transform((40, 40))
                for name, point in (("button_press_event", start), ("motion_notify_event", end), ("button_release_event", end)):
                    figure.canvas.callbacks.process(name, MouseEvent(name, figure.canvas, *point, button=1))
                for key in ("+", "s"):
                    figure.canvas.callbacks.process("key_press_event", KeyEvent("key_press_event", figure.canvas, key))
                saved = json.loads((photo_directory(args.output, "synthetic.png") / "summary.json").read_text())
                self.assertEqual(saved["roi"], [5, 5, 35, 35])
                self.assertEqual(saved["threshold"], 132)
                self.assertEqual(len(saved["particles"]), 1)
                self.assertEqual(figure.axes[3].tables[0][1, 1].get_text().get_text(), "400.0")
                for key in ("r", "-", "s"):
                    figure.canvas.callbacks.process("key_press_event", KeyEvent("key_press_event", figure.canvas, key))
                saved = json.loads((photo_directory(args.output, "synthetic.png") / "summary.json").read_text())
                self.assertEqual(saved["roi"], [0, 0, 180, 120])
                self.assertEqual(saved["threshold"], 127)
                self.assertEqual(len(saved["particles"]), 2)
                figure.canvas.callbacks.process("key_press_event", KeyEvent("key_press_event", figure.canvas, "q"))
                self.assertFalse(plt.fignum_exists(figure.number))

            with patch("matplotlib.pyplot.show", side_effect=exercise):
                interactive(self.image, "synthetic.png", args)

    def test_image_browsing_resets_roi_and_updates_source(self):
        with tempfile.TemporaryDirectory() as directory, matplotlib.rc_context():
            folder = Path(directory)
            first, second = folder / "a.png", folder / "b.png"
            cv2.imwrite(str(first), self.image)
            cv2.imwrite(str(second), np.zeros_like(self.image))
            args = SimpleNamespace(threshold=127, min_area=30, roi=(5, 5, 35, 35), invert=False, output=folder / "results")

            def exercise():
                figure = plt.gcf()
                for key in ("right", "s"):
                    figure.canvas.callbacks.process("key_press_event", KeyEvent("key_press_event", figure.canvas, key))
                saved = json.loads((photo_directory(args.output, second) / "summary.json").read_text())
                self.assertEqual(saved["source"], str(second.resolve()))
                self.assertEqual(saved["particles"], [])
                self.assertEqual(saved["roi"], [0, 0, 180, 120])
                for key in ("left", "s"):
                    figure.canvas.callbacks.process("key_press_event", KeyEvent("key_press_event", figure.canvas, key))
                saved = json.loads((photo_directory(args.output, first) / "summary.json").read_text())
                self.assertEqual(len(saved["particles"]), 2)
                self.assertIn("Saved:", figure.axes[-1].texts[0].get_text())
                plt.close(figure)

            with patch("matplotlib.pyplot.show", side_effect=exercise):
                interactive(self.image, first, args)

    def test_per_photo_export_does_not_overwrite_other_sources(self):
        with tempfile.TemporaryDirectory() as directory:
            result = analyze(self.image)
            first = save_photo(result, "/a/photo.jpg", directory)
            second = save_photo(result, "/b/photo.jpg", directory)
            self.assertNotEqual(first, second)
            save_photo(analyze(np.zeros_like(self.image)), "/a/photo.jpg", directory)
            self.assertEqual(len(json.loads((second / "summary.json").read_text())["particles"]), 2)
            with (Path(directory) / "photo_results.csv").open() as stream:
                self.assertEqual(len(list(csv.DictReader(stream))), 2)

    def test_smoothing_and_automatic_start(self):
        threshold = starting_threshold(self.image, 5)
        self.assertTrue(0 <= threshold <= 255)
        self.assertEqual(len(analyze(self.image, threshold, blur=5)["particles"]), 2)
        with self.assertRaises(ValueError):
            analyze(self.image, blur=4)


    def test_dashboard_empty_and_table_limit(self):
        figure, grid = plt.subplots(2, 2)
        try:
            result = analyze(np.zeros_like(self.image))
            draw_dashboard(figure, grid.ravel(), result, "empty.png")
            self.assertEqual(len(figure.axes[3].tables), 0)
            result["particles"] = [{"id": i+1, "area_px2": 400, "cx_px": 20, "cy_px": 20} for i in range(15)]
            draw_dashboard(figure, grid.ravel(), result, "many.png")
            self.assertIn("showing 12 of 15", figure.axes[3].get_title(loc="left"))
            self.assertEqual(len(figure.axes[3].tables[0].get_celld()), 26)
            self.assertEqual(len(figure.texts), 3)
        finally:
            plt.close(figure)


if __name__ == "__main__":
    unittest.main()