"""Local-only HTML workspace for the existing rice-analysis pipeline."""
import argparse
import base64
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import math
from pathlib import Path
from urllib.parse import urlparse, parse_qs
import webbrowser

import cv2
import numpy as np

from particle_counter import analyze, save_photo, starting_threshold

ROOT = Path(__file__).resolve().parent


def parameters(data):
    threshold = data.get("threshold", 127)
    minimum = data.get("min_area", 30)
    blur = data.get("blur", 5)
    roi = data.get("roi")
    if type(threshold) is not int or not 0 <= threshold <= 255:
        raise ValueError("Threshold must be an integer from 0 to 255")
    if type(minimum) not in (int, float) or not math.isfinite(minimum) or minimum < 0:
        raise ValueError("Minimum area must be finite and nonnegative")
    if type(blur) is not int or blur not in (0, 3, 5, 7):
        raise ValueError("Invalid smoothing kernel")
    if roi is not None and (not isinstance(roi, list) or len(roi) != 4 or any(type(v) is not int for v in roi)):
        raise ValueError("ROI must contain four integer coordinates")
    if type(data.get("invert", False)) is not bool:
        raise ValueError("Invert must be boolean")
    return dict(threshold=threshold, min_area=minimum, blur=blur, roi=roi, invert=data.get("invert", False))


class Handler(BaseHTTPRequestHandler):
    def send(self, content, content_type="application/json", status=200):
        if content_type == "application/json":
            content = json.dumps(content).encode()
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(content)

    def photo(self, identifier):
        if type(identifier) is not int or not 0 <= identifier < len(self.server.photos):
            raise ValueError("Unknown photo")
        path = self.server.photos[identifier]
        image = cv2.imread(str(path))
        if image is None:
            raise ValueError("Photo could not be decoded")
        return path, image

    def do_GET(self):
        parsed = urlparse(self.path)
        try:
            if parsed.path == "/api/photos":
                settings_path = ROOT / "dokumentasi/photo_settings.json"
                settings = json.loads(settings_path.read_text()) if settings_path.exists() else {}
                photos = []
                for i, path in enumerate(self.server.photos):
                    image = cv2.imread(str(path))
                    if image is None:
                        raise ValueError(f"Cannot decode {path.name}")
                    photos.append({"id": i, "name": path.name, "threshold": settings.get(path.name, 127),
                                   "min_area": round(image.shape[0] * image.shape[1] * 0.00004)})
                self.send({"folder": str(self.server.folder), "photos": photos})
            elif parsed.path == "/api/image":
                _, image = self.photo(int(parse_qs(parsed.query)["id"][0]))
                # Display copies only. Analysis and ROI coordinates use the original resolution.
                scale = min(1, 1200 / max(image.shape[:2]))
                display = cv2.resize(image, None, fx=scale, fy=scale) if scale < 1 else image
                self.send(cv2.imencode(".jpg", display)[1].tobytes(), "image/jpeg")
            elif parsed.path in ("/", "/app.js", "/style.css"):
                name, mime = {"/": ("index.html", "text/html; charset=utf-8"),
                              "/app.js": ("app.js", "text/javascript"),
                              "/style.css": ("style.css", "text/css")}[parsed.path]
                self.send((ROOT / "web" / name).read_bytes(), mime)
            else:
                self.send({"error": "Not found"}, status=404)
        except (ValueError, KeyError, IndexError) as error:
            self.send({"error": str(error)}, status=400)

    def do_POST(self):
        # Local tool, not a public hosting server. Reject foreign browser origins.
        allowed = f"http://127.0.0.1:{self.server.server_port}"
        if self.headers.get("Origin") not in (None, allowed, f"http://localhost:{self.server.server_port}"):
            self.send({"error": "Foreign origin rejected"}, status=403)
            return
        try:
            length = int(self.headers.get("Content-Length", 0))
            if not 0 < length <= 16384:
                raise ValueError("Invalid request size")
            data = json.loads(self.rfile.read(length))
            path, image = self.photo(data.get("id"))
            params = parameters(data)
            result = analyze(image, **params)
            if self.path == "/api/auto":
                self.send({"threshold": starting_threshold(image, params["blur"], params["roi"])})
            elif self.path == "/api/save":
                destination = save_photo(result, path, self.server.output)
                self.send({"output": str(destination), "count": len(result["particles"])})
            elif self.path == "/api/analyze":
                images = {}
                for key in ("overlay", "mask_numbered"):
                    display = result[key]
                    scale = min(1, 1400 / max(display.shape[:2]))
                    if scale < 1:
                        display = cv2.resize(display, None, fx=scale, fy=scale)
                    images[key] = "data:image/png;base64," + base64.b64encode(cv2.imencode(".png", display)[1]).decode()
                areas = [p["area_px2"] for p in result["particles"]]
                counts, edges = np.histogram(areas, bins=min(10, len(areas))) if areas else ([], [])
                self.send({"particles": result["particles"], "border_excluded": result["border_excluded"],
                           "width": image.shape[1], "height": image.shape[0], "roi": result["roi"],
                           "images": images, "histogram": {"counts": list(map(int, counts)), "edges": list(map(float, edges))}})
            else:
                self.send({"error": "Not found"}, status=404)
        except (ValueError, TypeError, KeyError, cv2.error) as error:
            self.send({"error": str(error)}, status=400)
        except OSError as error:
            self.send({"error": str(error)}, status=500)


def create_server(folder, output, port=8765):
    server = HTTPServer(("127.0.0.1", port), Handler)
    server.folder = Path(folder).resolve()
    server.photos = sorted(p for p in server.folder.iterdir() if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff") and p.is_file())
    server.output = Path(output)
    return server


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--photos", type=Path, default=ROOT.parent / "foto")
    parser.add_argument("--output", type=Path, default=ROOT / "outputs/web_dashboard")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    server = create_server(args.photos, args.output, args.port)
    address = f"http://127.0.0.1:{server.server_port}"
    print(f"Rice dashboard: {address} | {len(server.photos)} photos | Ctrl+C to stop", flush=True)
    if not args.no_browser:
        webbrowser.open(address)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()