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

from particle_counter import analyze, save_result, interactive


class CounterTests(unittest.TestCase):
    def setUp(self):
        self.image = np.zeros((120, 180, 3), np.uint8)
        cv2.rectangle(self.image, (10, 10), (30, 30), (255, 255, 255), -1)
        cv2.rectangle(self.image, (70, 50), (100, 80), (255, 255, 255), -1)

    def test_count_and_contour_area(self):
        result = analyze(self.image)
        self.assertEqual([p["area_px2"] for p in result["particles"]], [400, 900])

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
                for filename in ("overlay.png", "mask.png", "mask_numbered.png", "binary.png", "particles.csv", "summary.json", "histogram.png"):
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
                axis = figure.axes[0]
                start = axis.transData.transform((5, 5))
                end = axis.transData.transform((40, 40))
                for name, point in (("button_press_event", start), ("motion_notify_event", end), ("button_release_event", end)):
                    figure.canvas.callbacks.process(name, MouseEvent(name, figure.canvas, *point, button=1))
                for key in ("+", "s"):
                    figure.canvas.callbacks.process("key_press_event", KeyEvent("key_press_event", figure.canvas, key))
                saved = json.loads((args.output / "summary.json").read_text())
                self.assertEqual(saved["roi"], [5, 5, 35, 35])
                self.assertEqual(saved["threshold"], 132)
                self.assertEqual(len(saved["particles"]), 1)
                for key in ("r", "-", "s"):
                    figure.canvas.callbacks.process("key_press_event", KeyEvent("key_press_event", figure.canvas, key))
                saved = json.loads((args.output / "summary.json").read_text())
                self.assertEqual(saved["roi"], [0, 0, 180, 120])
                self.assertEqual(saved["threshold"], 127)
                self.assertEqual(len(saved["particles"]), 2)
                figure.canvas.callbacks.process("key_press_event", KeyEvent("key_press_event", figure.canvas, "q"))
                self.assertFalse(plt.fignum_exists(figure.number))

            with patch("matplotlib.pyplot.show", side_effect=exercise):
                interactive(self.image, "synthetic.png", args)


if __name__ == "__main__":
    unittest.main()