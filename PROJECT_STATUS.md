# Change Evidence Project Status

> Last verified: 2026-08-20  
> Purpose: AI coding agents (Cursor, Cline, etc.) can quickly understand the current project state before making changes.

---

## 1. Project Purpose

**Change Evidence MVP** is a drone/satellite imagery change-detection pipeline. It converts GeoTIFF inputs into viewable PNGs, then provides a manual alignment tool so before/after image pairs can be registered via control points. Later steps (alignment output, masks, change analysis) are planned but not yet implemented.

---

## 2. Current Development Stage

| Step | Name | Status |
|------|------|--------|
| STEP 1-A | GeoTIFF → PNG conversion | **Implemented** (script exists and runs) |
| STEP 1-B | GeoTIFF metadata extraction → JSON | **Partial** (helper functions exist; not wired to `main()`) |
| STEP 2 | Manual alignment GUI (control points) | **Partial** (CP input UI done; affine/warp/save not done) |
| STEP 3+ | Aligned output, masks, change detection | **Not started** |

---

## 3. Project Structure

```
change-evidence-engine/
├── LICENSE
├── README.md
├── PROJECT_STATUS.md          ← this file
├── .vscode/settings.json
├── projects/
│   ├── tif/                   # Original GeoTIFF inputs (4 files)
│   ├── png/                   # Derived PNGs (4 files)
│   ├── metadata/              # Empty (no JSON yet)
│   ├── aligned/               # Empty (placeholder)
│   └── masks/                 # Empty (placeholder)
├── src/
│   ├── convert_tif_to_png.py  # STEP 1 entry point
│   └── align/
│       ├── align_images.py    # STEP 2 GUI entry point
│       ├── image_view.py
│       ├── control_points.py
│       ├── affine.py          # Empty (0 bytes)
│       ├── polygon.py         # Empty (0 bytes)
│       └── project_io.py      # Empty (0 bytes)
└── venv/                      # Local virtualenv (not tracked in git)
```

**Git-tracked source files:** 7 Python files under `src/`  
**No** `requirements.txt` or `pyproject.toml` at project root.

---

## 4. Input Data

`projects/tif/` contains **4 GeoTIFF files** (original data; do not modify):

| File | Approx. size |
|------|--------------|
| `seoul_park_1PM.tif` | 28.06 MB |
| `seoul_park_3PM.tif` | 31.41 MB |
| `speeddom_1330.tif` | 23.56 MB |
| `speeddom_1430.tif` | 20.68 MB |

**Suggested before/after pairs for alignment testing:**

- `seoul_park_1PM` ↔ `seoul_park_3PM`
- `speeddom_1330` ↔ `speeddom_1430`

---

## 5. Generated Data

| Path | Status |
|------|--------|
| `projects/png/` | **4 PNG files** — derived from TIF (same basenames) |
| `projects/metadata/` | **Empty folder** — no `image_metadata.json` |
| `projects/aligned/` | **Empty folder** — no aligned outputs |
| `projects/masks/` | **Empty folder** — no mask files |

**PNG files in `projects/png/`:**

| File | Approx. size |
|------|--------------|
| `seoul_park_1PM.png` | 18.22 MB |
| `seoul_park_3PM.png` | 20.39 MB |
| `speeddom_1330.png` | 14.98 MB |
| `speeddom_1430.png` | 12.91 MB |

---

## 6. STEP 1 Status

### GeoTIFF → PNG (`src/convert_tif_to_png.py`)

| Item | Status |
|------|--------|
| File exists | **Yes** |
| File empty | **No** (~166 lines) |
| Scans `projects/tif/*.tif` | **Yes** |
| Writes to `projects/png/*.png` | **Yes** |
| Band → RGB conversion | **Yes** (1/2/3+ bands handled) |
| dtype normalization → uint8 | **Yes** |
| Existing PNG files present | **Yes** (4 files) |
| Original TIF location | `projects/tif/` |

### GeoTIFF Metadata (STEP 1-B, same file)

| Item | Status |
|------|--------|
| `_extract_metadata()` | **Implemented** (not called from `main()`) |
| `_write_metadata_file()` | **Implemented** (not called from `main()`) |
| Output `projects/metadata/image_metadata.json` | **Not generated yet** |

### How to run STEP 1-A

```bash
python src/convert_tif_to_png.py
```

Requires: `rasterio`, `pillow` (available in system Python and `venv`).

**Note:** Running the script overwrites existing PNGs in `projects/png/`.

---

## 7. STEP 2 Status

Entry point: `src/align/align_images.py`  
Run from `src/align/` using project `venv` (needs `opencv-python`, `PySide6`):

```bash
cd src/align
..\..\venv\Scripts\python.exe align_images.py
```

| Feature | Status |
|---------|--------|
| GUI (PySide6 main window) | **Implemented** |
| ImageView (display, click coords) | **Implemented** |
| Control Point data model | **Implemented** (`control_points.py`) |
| Point Wizard (T1 → T2 sequential input) | **Implemented** |
| Point display (red circle + label on both views) | **Implemented** |
| Point edit (select in tree, click to update) | **Implemented** |
| Point delete | **Implemented** |
| Point reset (clear all) | **Implemented** |
| Load images (file dialog, PNG only) | **Implemented** |
| `ready_for_alignment()` (≥3 complete CPs) | **Implemented in code** — not used in UI |
| Affine transform calculation | **Not implemented** (`affine.py` empty) |
| Warp / apply transform | **Not implemented** |
| Overlay (before/after blend) | **Not implemented** |
| Polygon ROI | **Not implemented** (`polygon.py` empty) |
| Project save / load | **Not implemented** (`project_io.py` empty) |
| Auto-load from `projects/png/` | **Not implemented** |
| Zoom / pan | **Not implemented** (`NoDrag`, `fitInView` only) |

---

## 8. Dependencies

### Project venv (`venv/`, Python 3.14.5)

Primary environment for STEP 2; also supports STEP 1.

| Package | Version |
|---------|---------|
| rasterio | 1.5.0 |
| pillow | 12.2.0 |
| opencv-python | 5.0.0.93 |
| PySide6 | 6.11.1 |
| numpy | 2.5.0 |
| affine | 2.4.0 |

### System Python (`C:\Python314\python.exe`, 3.14.5)

Usable for STEP 1 only (no OpenCV / PySide6):

| Package | Version |
|---------|---------|
| rasterio | 1.5.1 |
| pillow | 12.3.0 |
| numpy | 2.5.1 |

---

## 9. Important Development Rules

- `projects/tif/` is **original source data** — never modify TIF files.
- PNG files are **derived** from TIF and can be regenerated.
- Existing PNGs **may be overwritten** when re-running STEP 1-A.
- Do **not** unnecessarily change existing STEP 2 code that already works.
- **Preserve** the current project layout (`projects/`, `src/align/` structure).
- Implement in **small, verifiable steps**.
- **Analyze existing code** before implementing new features.
- Avoid **unnecessary refactoring**.
- **Validate one STEP** before moving to the next.

---

## 10. Next Development Step

**Immediate goal: complete STEP 1**

1. GeoTIFF → PNG (STEP 1-A) — already working; verify on sample TIFs if needed.
2. GeoTIFF metadata → `projects/metadata/image_metadata.json` (STEP 1-B) — wire `_extract_metadata()` and `_write_metadata_file()` into `main()` in `src/convert_tif_to_png.py`.

After STEP 1 is verified end-to-end, proceed to STEP 2 backend: implement `src/align/affine.py` and connect alignment execution in `align_images.py`.
