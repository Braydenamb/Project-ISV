# Rice counter — UAS ISV Topic 10

Local photo analysis with OpenCV and an HTML/CSS/JavaScript dashboard.
Select a photo, adjust threshold or ROI, inspect the numbered detections, and save.

## Run

```bash
cd "/home/miq/Documents/ISV/Project ISV/Project"
.venv/bin/python web_app.py
```

The dashboard opens on localhost, port 8765. Stop with Ctrl+C.
Optional arguments: `--no-browser`, `--port 8766`, and `--photos /absolute/photo/folder`.
The default photos are in `/home/miq/Documents/ISV/Project ISV/foto`.
Dependencies are listed in `/home/miq/Documents/ISV/Project ISV/Project/requirements.txt`.

- Drag on the image to select an ROI; Reset ROI restores the full image.
- Use `+` / `-` for threshold, left/right arrows for photos, and `S` to save.
- Settings trigger detection immediately, without an artificial adjustment pause.
  If analysis is already running, the latest settings are processed as soon as it
  finishes, rather than queuing every key press. Previous results stay visible;
  Save is disabled until analysis with the current settings completes.
- Advanced settings and measurements are expandable.
- Settings last only until page reload. Save before refreshing.
- **Start live camera** requests camera permission and continuously counts the current
  frame. **Stop camera**, selecting a photo, or leaving the page releases the camera.
- Live frames are scaled to at most 960 pixels per side and sent only to this local
  Python server. Analysis requests run sequentially with a 200 ms pause between them;
  this is near-real-time inspection, not guaranteed video-rate processing.
- ROI and minimum areas in camera mode refer to the scaled frame pixels, not the
  original camera resolution. Keep the camera still, use even lighting and separated grains.
- The live count is **per frame**, not a cumulative count or tracked grain total.
  It can fluctuate, and touching grains may still merge.
- Save in camera mode exports the last analyzed frame, its original image and results
  into a new unique folder under `outputs/web_dashboard/camera/`. Live frames are
  otherwise not saved. Allow browser camera permission on localhost; no microphone is requested.
- Exports go to `/home/miq/Documents/ISV/Project ISV/Project/outputs/web_dashboard`.
  Saving the same photo replaces that photo's previous export, not other photos.

## Repository layout

All paths below are relative to `/home/miq/Documents/ISV/Project ISV/Project`.

| Location | Purpose |
| --- | --- |
| `web_app.py` | Local server and dashboard API |
| `particle_counter.py` | Shared analysis, exports, optional desktop UI |
| `web/` | HTML, CSS, plain JavaScript |
| `tests/` | Unit/API tests and optional browser workflow test |
| `docs/` | Assignment rules and verification history |
| `dokumentasi/` | Photo settings, experiment notes, screenshots |
| `data/` | Local development datasets; generated/raw data ignored by Git |
| `outputs/` | Generated analysis exports; ignored by Git |

Original photos, the assignment DOCX, and the friend's `UAS_ISV` folder remain outside this app folder and are unchanged.

## Test

Run from `/home/miq/Documents/ISV/Project ISV/Project`:

```bash
.venv/bin/python -m unittest discover -s tests -v
node --check web/app.js
```

With the dashboard server running on port 8765, the optional browser test is:

```bash
.venv/bin/python -m tests.browser_smoke
```

It requires the already-installed Playwright testing package and Chromium.
It saves a test analysis and updates the dashboard screenshot.

The independent camera browser check starts its own temporary server and uses a
synthetic video stream instead of a physical camera. It requires the same browser tools:

```bash
.venv/bin/python -m tests.camera_browser_smoke
```

## Limits

Detection includes conservative shape rejection: solidity below 0.55,
compactness below 0.08, or foreground coverage below 0.35 inside an external
contour is excluded. The dashboard reports these exclusions separately from
boundary exclusions, and exports record the filter settings. This reduces
branching floor texture and sparse bright rings, but does not identify rice
semantically. Smooth bright floor patches can still pass; irregular or touching
grains can be rejected. Inspect masks and use an ROI to exclude background.

- Counts are accepted connected contours, not validated grain totals.
- Touching grains can merge; background texture can cause false detections.
- Boundary-touching objects are excluded.
- Areas are uncalibrated projected contour areas in px², not mm².
- No manual-reference accuracy study or physical calibration has been completed.
- Local use only; do not expose this server publicly.

Assignment requirements: `/home/miq/Documents/ISV/Project ISV/Project/docs/RULES.md`.
Verification history: `/home/miq/Documents/ISV/Project ISV/Project/docs/VERIFICATION.md`.
Use this README for current launch and test commands. The verification document
is a historical record; references to retired helper scripts are not current instructions.