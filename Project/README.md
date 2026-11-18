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
- Advanced settings and measurements are expandable.
- Settings last only until page reload. Save before refreshing.
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

## Limits

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