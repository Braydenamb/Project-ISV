import json
from pathlib import Path
import tempfile
import threading
import unittest
from urllib.request import Request, urlopen
from urllib.error import HTTPError

import cv2
import numpy as np

from web_app import create_server


class WebTests(unittest.TestCase):
    def test_http_analysis_save_and_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            image = np.zeros((100, 100, 3), np.uint8)
            cv2.rectangle(image, (20, 20), (40, 40), (255, 255, 255), -1)
            cv2.imwrite(str(root / "rice.png"), image)
            server = create_server(root, root / "results", 0)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            address = f"http://127.0.0.1:{server.server_port}"

            def request(path, body=None, origin=None):
                headers = {"Content-Type": "application/json"}
                if origin:
                    headers["Origin"] = origin
                return urlopen(Request(address + path, data=json.dumps(body).encode() if body is not None else None, headers=headers))

            try:
                self.assertIn(b"Rice counter", request("/").read())
                self.assertEqual(len(json.load(request("/api/photos"))["photos"]), 1)
                body = dict(id=0, threshold=127, min_area=30, blur=0, roi=None, invert=False)
                data = json.load(request("/api/analyze", body))
                self.assertEqual(len(data["particles"]), 1)
                self.assertEqual(data["particles"][0]["area_px2"], 400)
                self.assertEqual(sum(data["histogram"]["counts"]), 1)
                self.assertEqual(data["width"], 100)
                saved = json.load(request("/api/save", body))
                self.assertTrue((Path(saved["output"]) / "particles.csv").exists())
                for invalid in ({**body, "threshold": 999}, {**body, "id": -1}, {**body, "roi": [0, 0, 1000, 1]}, {**body, "min_area": float("nan")}):
                    with self.assertRaises(HTTPError) as error:
                        request("/api/analyze", invalid)
                    self.assertEqual(error.exception.code, 400)
                    error.exception.close()
                with self.assertRaises(HTTPError) as error:
                    request("/api/save", body, "https://untrusted.example")
                self.assertEqual(error.exception.code, 403)
                error.exception.close()
            finally:
                server.shutdown()
                server.server_close()
                thread.join()


if __name__ == "__main__":
    unittest.main()