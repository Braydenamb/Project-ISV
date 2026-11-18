import json
import base64
from http.client import HTTPConnection
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
    def test_camera_analysis_validation_and_snapshot_exports(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            server = create_server(root, root / "results", 0)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            address = f"http://127.0.0.1:{server.server_port}"

            def request(path, body, origin=None):
                headers = {"Content-Type": "application/json"}
                if origin:
                    headers["Origin"] = origin
                with urlopen(Request(address + path, data=json.dumps(body).encode(), headers=headers)) as response:
                    return json.load(response)

            image = np.zeros((120, 160, 3), np.uint8)
            cv2.rectangle(image, (20, 20), (40, 40), (255, 255, 255), -1)
            frame = "data:image/jpeg;base64," + base64.b64encode(cv2.imencode(".jpg", image)[1]).decode()
            body = dict(frame=frame, threshold=127, min_area=30, blur=0, roi=None, invert=False)
            try:
                result = request("/api/camera/analyze", body)
                self.assertEqual(len(result["particles"]), 1)
                self.assertEqual((result["width"], result["height"]), (160, 120))
                self.assertEqual(sum(result["histogram"]["counts"]), 1)
                self.assertEqual(result["background_excluded"], 0)
                self.assertFalse((root / "results").exists())
                self.assertIn("threshold", request("/api/camera/auto", body))
                saved = request("/api/camera/save", body)
                second = request("/api/camera/save", {**body, "threshold": 255})
                self.assertNotEqual(saved["output"], second["output"])
                self.assertEqual(second["count"], 0)
                destination = Path(saved["output"])
                self.assertTrue((destination / "original.png").is_file())
                self.assertTrue((destination / "particles.csv").is_file())
                np.testing.assert_array_equal(cv2.imread(str(destination / "original.png")),
                                              cv2.imdecode(cv2.imencode(".jpg", image)[1], cv2.IMREAD_COLOR))
                metadata = json.loads((destination / "summary.json").read_text())
                self.assertEqual(metadata["source"], str(destination / "original.png"))
                for invalid in ({**body, "frame": "bad"}, {**body, "frame": "data:image/jpeg;base64,!!!"},
                                {**body, "frame": "data:image/jpeg;base64,"}, {**body, "roi": [0, 0, 999, 2]},
                                {**body, "threshold": 300}, []):
                    with self.assertRaises(HTTPError) as error:
                        request("/api/camera/analyze", invalid)
                    self.assertEqual(error.exception.code, 400)
                    error.exception.close()
                # Send only oversized headers: the server rejects before reading the body.
                # Uploading megabytes here races the server closing the connection.
                connection = HTTPConnection("127.0.0.1", server.server_port, timeout=5)
                try:
                    connection.putrequest("POST", "/api/camera/analyze")
                    connection.putheader("Content-Length", str(2 * 1024 * 1024 + 1))
                    connection.endheaders()
                    response = connection.getresponse()
                    self.assertEqual(response.status, 400)
                    response.read()
                finally:
                    connection.close()
                with self.assertRaises(HTTPError) as error:
                    request("/api/camera/save", body, "https://untrusted.example")
                self.assertEqual(error.exception.code, 403)
                error.exception.close()
            finally:
                server.shutdown()
                server.server_close()
                thread.join()

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
                self.assertEqual(data["background_excluded"], 0)
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