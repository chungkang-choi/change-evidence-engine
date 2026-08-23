# Change Evidence Project Status

> Last verified: 2026-08-23 (STEP 2-F update)
> Purpose: AI coding agents (Cursor, Cline, etc.) can quickly understand the current project state before making changes.
> This document only contains verified facts about the actual codebase. Do not add speculative or planned content as if it were already implemented.

> **Note on source material**: Section 1–2 and Sections 10–14 below incorporate the vision, pipeline design, and principles from the "Change Evidence Service MVP Development Specification v6.0" planning note. That note's own STEP 1 status claim ("`convert_tif_to_png.py` exists but is empty") does **not** match this repository's actual state — in this codebase, STEP 1 has already been implemented and verified (see Section 6). Wherever the v6.0 note and the actual code disagree, **this document follows the actual code**, not the note.

---

## 1. Project Purpose & MVP Goal

**One-line definition**: Align drone orthomosaic images of the same location taken at different times to a common reference frame, correct brightness differences, automatically extract changed regions, and present the results as human-understandable Visual Evidence.

**1-month goal**: Not a finished SaaS product. The goal is an MVP + portfolio that can explain the service's value to a manufacturing-industry customer in 30 seconds.

**MVP success criteria**:
- Changes are visibly confirmable in real imagery.
- A non-expert can understand the result.
- A manufacturing-industry use case can be explained with it.
- It can be used in customer meetings and as a portfolio piece.
- The same project can be re-run repeatably.

---

## 2. Business & Development Stage

```
사업 아이디어              ✅ 완료
    ↓
시장 조사 / 사업 기획      ✅ 완료
    ↓
PoC 데이터 확보            ✅ 완료
    ↓
MVP 구현                   ◀ 현재 (STEP 1 + STEP 2-A~F complete, STEP 3+ not started)
    ↓
포트폴리오 제작
    ↓
잠재 고객 조사
    ↓
파일럿 영업
    ↓
첫 고객 확보
```

---

## 3. Current Technical Implementation Status

| Step | Name | Status |
|------|------|--------|
| STEP 1 | GeoTIFF → PNG conversion + Metadata extraction | **✅ Implemented & verified** |
| STEP 2-A | Alignment GUI + Control Point input/edit/delete/reset | **✅ Implemented & verified** |
| STEP 2-B | Control Point → Affine Matrix (`compute_affine`) | **✅ Implemented & verified** |
| STEP 2-C | Affine Matrix → T2 Warp (`warp_image`) | **✅ Implemented & verified** |
| STEP 2-D | T1 + Aligned T2 Overlay + Opacity Slider + "Run Alignment" button | **✅ Implemented & verified** (committed) |
| STEP 2-E | GSD comparison (Ratio/Difference) + GUI info display | **✅ Implemented & verified** (committed) |
| STEP 2-F | Project Save / Load (`project_io.py`) | **✅ Implemented & verified** (uncommitted — see Section 9) |
| STEP 2 remaining | GSD Resampling, Pixel Frame unification, Polygon ROI | **❌ Not implemented** |
| STEP 3 | Brightness Normalization | **❌ Not started** |
| STEP 4 | Change Detection | **❌ Not started** |
| STEP 5 | Region Extraction | **❌ Not started** |
| STEP 6 | Visualization | **❌ Not started** |
| STEP 7 | Report | **❌ Not started** |

**Current most important next task**: decide whether to commit STEP 2-F, then move on to Polygon ROI or proceed directly to STEP 3, per user decision.

---

## 4. Project Structure

### 4.1 Current actual structure (verified on disk)

```
change-evidence-engine/
├── LICENSE
├── README.md
├── PROJECT_STATUS.md          ← this file
├── .vscode/settings.json
├── projects/
│   ├── tif/                   # Original GeoTIFF inputs (4 files, do not modify)
│   ├── png/                   # Derived PNGs (4 files)
│   ├── metadata/              # image_metadata.json (generated)
│   ├── aligned/                # aligned_<T2>_<timestamp>.png files (STEP 2-C/D output, one per Run Alignment execution)
│   └── masks/                 # Empty (placeholder, unused)
├── src/
│   ├── convert_tif_to_png.py  # STEP 1 entry point — fully implemented
│   └── align/
│       ├── align_images.py    # STEP 2 GUI entry point (STEP 2-A/B/C/D/E/F wired in)
│       ├── image_view.py
│       ├── control_points.py
│       ├── affine.py          # compute_affine() + warp_image() (STEP 2-B/2-C)
│       ├── polygon.py         # Empty (0 bytes) — not implemented
│       └── project_io.py      # save_project()/load_project() + helpers (STEP 2-F) — implemented
├── .gitignore                 # excludes __pycache__/, *.pyc, venv/
└── venv/                      # Local virtualenv (not tracked in git)
```

**Git-tracked source files:** 7 Python files under `src/`.
**No** `requirements.txt` or `pyproject.toml` at project root.

### 4.2 Target future structure (per v6.0 spec — not yet created, for reference only)

Do **not** pre-create these files/directories. Add them only when the corresponding STEP is actually implemented.

```
ChangeEvidence/
├── project/
│   ├── tif/
│   ├── png/
│   ├── metadata/
│   ├── aligned/
│   ├── masks/
│   └── output/
└── src/
    ├── convert_tif_to_png.py
    ├── align/
    │   ├── affine.py
    │   ├── align_images.py
    │   ├── control_points.py
    │   ├── image_view.py
    │   ├── polygon.py
    │   └── project_io.py
    ├── normalize_brightness.py        # STEP 3 (not started)
    ├── change/                        # STEP 4 (not started)
    │   ├── detect_change.py
    │   ├── morphology.py
    │   ├── contour.py
    │   ├── region.py
    │   └── summary.py
    ├── visualize/                     # STEP 6 (not started)
    │   └── visualize_change.py
    └── report/                        # STEP 7 (not started)
        └── create_report.py
```

---

## 5. PoC Data & Known Real-World Problems

**서울대공원 (Seoul Grand Park)**: same location, repeat capture; orthomosaic generation complete.
**광명스피돔 (Gwangmyeong Speedom)**: same location, repeat capture; orthomosaic generation complete; vehicle-position changes confirmed.

**Confirmed problem**: naively comparing two GeoTIFFs directly does not produce stable change detection, because of:

- GPS error
- WebODM processing differences between flights
- Differences in capture position
- Differences in capture altitude
- Pixel resolution (GSD) differences
- Lighting/illumination differences
- Shadow changes
- Image edge distortion

This is why the pipeline in Section 9 explicitly separates **Metadata capture → Baseline Frame creation → Brightness Normalization → Change Detection** into distinct steps rather than diffing raw GeoTIFFs.

---

## 6. Input Data (verified on disk)

`projects/tif/` contains **4 GeoTIFF files** (original data; do not modify):

| File | Approx. size |
|------|--------------|
| `seoul_park_1PM.tif` | 28.06 MB |
| `seoul_park_3PM.tif` | 31.41 MB |
| `speeddom_1330.tif` | 23.56 MB |
| `speeddom_1430.tif` | 20.68 MB |

**Before/after pairs used for alignment testing:**

- `seoul_park_1PM` (T1) ↔ `seoul_park_3PM` (T2)
- `speeddom_1330` (T1) ↔ `speeddom_1430` (T2)

---

## 7. Generated Data

| Path | Status |
|------|--------|
| `projects/png/` | **4 PNG files** — derived from TIF (same basenames), pixel-identical dimensions to source TIF |
| `projects/metadata/` | **`image_metadata.json` present** — generated for all 4 TIFs |
| `projects/aligned/` | Output of the GUI's "Run Alignment" button (STEP 2-D). Filenames are `aligned_<T2 stem>_<YYYYMMDD_HHMMSS>.png` — **each Run Alignment execution creates a new, uniquely-named file** and never overwrites a previous result or the original T1/T2 PNG inputs (fixed after STEP 2-F; previously it always overwrote a fixed `aligned_<T2>.png` name). Currently contains one pre-existing tracked file (`aligned_seoul_park_3PM.png`, from before this fix) plus one untracked leftover (`aligned_speeddom_1430.png`). |
| `projects/masks/` | **Empty folder** — no mask files (STEP 4, not started) |
| `projects/project.json` | **Not present by default** — STEP 2-F's "Save Project" suggests this path as the default save location (see Section 9), but no project file has been committed to the repo yet. |

**`projects/metadata/image_metadata.json`** — single JSON keyed by TIF filename, containing per-file: `filename`, `width`, `height`, `band_count`, `dtype`, `crs`, `transform` (6 affine coefficients), `pixel_size_x`, `pixel_size_y`, `gsd`. All 4 TIFs use `EPSG:32652`.

Real GSD values (from actual metadata, used in STEP 2-E verification):

| File | GSD (m/pixel) |
|------|----------------|
| `seoul_park_1PM.tif` (T1) | 0.05356638 |
| `seoul_park_3PM.tif` (T2) | 0.05299648 |
| `speeddom_1330.tif` (T1) | 0.05423241 |
| `speeddom_1430.tif` (T2) | 0.05359093 |

GSD Ratio (T2/T1): Seoul Park ≈ 0.9894 (1.06% difference), Speeddom ≈ 0.9882 (1.18% difference) — both classified as "Small GSD difference" (see Section 9).

---

## 8. STEP 1 Status — GeoTIFF → PNG + Metadata

### `src/convert_tif_to_png.py` (176 lines)

| Item | Status |
|------|--------|
| File exists / not empty | **Yes** |
| Scans `projects/tif/*.tif` | **Yes** |
| Writes to `projects/png/*.png` | **Yes** |
| Band → RGB conversion | **Yes** (1/2/3+ bands handled) |
| dtype normalization → uint8 | **Yes** |
| `_extract_metadata()` | **Implemented**, called from `main()` |
| `_write_metadata_file()` | **Implemented**, called from `main()` — writes `projects/metadata/image_metadata.json` |
| Verified against real TIFs | **Yes** — width/height/band_count/dtype/crs/transform/pixel_size/gsd cross-checked exactly against all 4 real TIFs |

### How to run STEP 1

```bash
python src/convert_tif_to_png.py
```

Requires: `rasterio`, `pillow`.
**Note:** Running this script overwrites existing PNGs in `projects/png/` and regenerates `projects/metadata/image_metadata.json`.

---

## 9. STEP 2 Status — Baseline Reference Frame / Alignment Tool

Entry point: `src/align/align_images.py`
Run from `src/align/` using project `venv` (needs `opencv-python`, `PySide6`):

```bash
cd src/align
..\..\venv\Scripts\python.exe align_images.py
```

| Feature | Status |
|---------|--------|
| GUI (PySide6 main window) | **✅ Implemented** |
| ImageView (display, click coords) | **✅ Implemented** |
| Control Point data model (`control_points.py`) | **✅ Implemented** |
| Point Wizard (T1 → T2 sequential input, `P1`, `P2`, ...) | **✅ Implemented** |
| Point display (red circle + label on both views) | **✅ Implemented** |
| Point edit / delete / reset | **✅ Implemented** |
| Load images (file dialog, PNG only) | **✅ Implemented** |
| Affine transform calculation (`compute_affine()` in `affine.py`) | **✅ Implemented** — `cv2.estimateAffine2D`, T2 → T1 direction, min 3 points, verified (max reprojection error 0.0003px on real georeferenced points) |
| Warp (`warp_image()` in `affine.py`) | **✅ Implemented** — `cv2.warpAffine`, output size = T1 pixel dimensions (dynamic, no hardcoding) |
| "Run Alignment" button wiring `compute_affine()` + `warp_image()` into GUI | **✅ Implemented** — gated on ≥3 completed Control Points |
| Overlay (T1 + aligned T2, `QGraphicsPixmapItem` two-layer) | **✅ Implemented** |
| Opacity Slider (0–100, real-time via `setOpacity()`) | **✅ Implemented** |
| Aligned image auto-save (`projects/aligned/aligned_<T2>_<timestamp>.png`) | **✅ Implemented** — each Run Alignment execution writes a new, uniquely-timestamped file; never overwrites a previous result or the original input PNGs |
| GSD Ratio / Difference calculation + GUI info display | **✅ Implemented** (STEP 2-E, see detail below) |
| Project Save / Load (`project_io.py`) | **✅ Implemented** (STEP 2-F, see detail below) |
| GSD Resampling / normalization | **❌ Not implemented** — intentionally deferred (see STEP 2-E conclusion below) |
| Pixel Frame unification (`pixel_frame.json`) | **❌ Not implemented** |
| Polygon ROI (`polygon.py`) | **❌ Not implemented** (file empty) |
| Auto-load from `projects/png/` | **❌ Not implemented** (manual file dialog only) |
| Zoom / pan | **❌ Not implemented** (`NoDrag`, `fitInView` only) |

### `affine.py` detail (STEP 2-B / STEP 2-C, unchanged since implementation)

| Item | Status |
|------|--------|
| `compute_affine(control_points)` | Reads `point.t1`/`point.t2`; returns 2×3 `numpy.ndarray` or `None` if fewer than 3 completed points. Uses `cv2.estimateAffine2D` (full 6-DOF, not `estimateAffinePartial2D`) so it can absorb non-uniform scale/GSD differences between T1 and T2. |
| `warp_image(image, affine_matrix, output_size)` | Thin wrapper around `cv2.warpAffine`; does not recompute or invert the matrix. |
| Direction | T2 → T1 (verified) |
| Metadata/CRS usage inside `affine.py` | **None by design** — Control Points are plain PNG pixel coordinates, not world coordinates |

### STEP 2-E detail — GSD comparison & display (observation only, no resampling)

- **Formulas**: `GSD Ratio = T2_gsd / T1_gsd`; `GSD Difference(%) = abs(T2_gsd - T1_gsd) / T1_gsd × 100`.
- **Status classification (informational only, not a pass/fail or resampling trigger)**: `<5%` → "Small GSD difference", `5–20%` → "Moderate GSD difference", `>20%` → "Large GSD difference" (shows an additional warning message but does not block/alter Alignment).
- **GSD = None / metadata file missing**: handled gracefully — displays `N/A` / `GSD unavailable` / `image_metadata.json not found`, without crashing and without blocking the Alignment workflow.
- **Verified conclusion**: for the current real data (GSD differences ~1–1.2%), the existing 6-DOF `compute_affine()` (via `cv2.estimateAffine2D`) already absorbs the GSD/scale difference implicitly, since Control Points are picked at matching real-world locations in each image's own native pixel grid. The computed affine scale factor for the Seoul Park pair (~0.9894) matches the real GSD ratio (0.989361) to 5 decimal places. **No separate GSD resampling step is required for current data.** This should be revisited if a future dataset has a much larger GSD difference.
- **Files touched**: only `src/align/align_images.py` (new module-level helper functions + `update_gsd_info()` method + `gsd_info_label` widget in the Overlay panel). `affine.py`, `image_view.py`, `control_points.py`, `polygon.py`, `project_io.py`, and `image_metadata.json` were **not** modified.
- **Commit status**: **committed** (`80a8eeb`).

### STEP 2-F detail — Project Save / Load

- **Files touched**: `src/align/project_io.py` (implemented from the previously-empty file) and `src/align/align_images.py` (Save/Load buttons + minimal state additions). `affine.py`, `image_view.py`, `control_points.py`, `polygon.py` were **not** modified.
- **`project_io.py`** is pure Python (no Qt dependency): `get_project_root()`, `to_relative_path()`/`to_absolute_path()`, `control_points_to_list()`/`restore_control_points()`, `affine_matrix_to_list()`/`affine_matrix_from_list()`, `build_project_dict()`, `save_project()`, `load_project()`.
- **`project.json` structure** (version 1): `t1_image`/`t2_image` (paths relative to project root, e.g. `projects/png/seoul_park_1PM.png`), `control_points` (list of `{name, t1, t2}`, only points with at least one coordinate set are saved), `affine_matrix` (2×3 list-of-lists or `null`), `aligned_image` (relative path or `null`).
- **New MainWindow state** (previously only local variables): `self.affine_matrix` (set in `run_alignment()`), `self.aligned_image_path` (set in `_save_aligned_image()`). Both are required so Save Project can persist the exact computed values without recomputation.
- **`affine.py`/`control_points.py` are not touched**: Affine values are saved/restored as-is (no recomputation), and `ControlPointManager`'s existing public attributes/methods (`points`, `current_point`, `current_index`, `state`, `create_next_point()`) are reused directly to restore Wizard state — no new Control Point system was created.
- **GSD stays out of `project.json`**: GSD is not duplicated into the project file; `image_metadata.json` remains the single source of truth, looked up fresh via `update_gsd_info()` after Load.
- **Verified with real data** (`seoul_park_1PM`/`seoul_park_3PM`): full round-trip (load → 4 Control Points → Run Alignment → Save Project → new `MainWindow` instance → Load Project) reproduced **byte-identical** Control Point coordinates and an **exactly identical** Affine Matrix (no floating-point drift), correctly restored the Overlay, and Opacity 0/50/100 worked identically after load.
- **Exception handling verified**: (1) saving/loading before Alignment has been run → `affine_matrix`/`aligned_image` correctly saved and restored as `null`, no crash; (2) T1 image file missing at load time → load aborted with `"Project load failed: T1 image not found."`, no partial/corrupted state; (3) aligned image file missing but T1/T2/CP/Affine present → images, Control Points, and Affine Matrix are still restored, Overlay is simply not shown, with message `"...Aligned image not found. Control Points and image state were restored."`; (4) `project.json` file itself missing → clear `"Project load failed: ..."` message, no crash.
- **Default save location**: "Save Project" suggests `projects/project.json` (via `QFileDialog.getSaveFileName`, user can change it). This location was chosen because the current `projects/` structure is flat (`tif/`, `png/`, `metadata/`, `aligned/`, `masks/` are siblings, not per-project subfolders), so a single `project.json` alongside them is the most natural fit for now — this may need revisiting if multi-project support is added later.
- **Commit status**: implemented and verified, but **not yet committed** (`git status` shows `M src/align/align_images.py`, `M src/align/project_io.py`).

---

## 10. STEP 3–7 — Planned Design (not implemented, reference only)

The following is the target pipeline design from the v6.0 specification. **None of this exists in code yet.** It is recorded here so future steps follow a consistent design instead of being re-derived from scratch.

```
Drone Image → GeoTIFF
  → STEP 1: GeoTIFF → PNG + Metadata Extraction
  → STEP 2: Baseline Reference Frame
      Control Points → Affine → Warp → GSD/Pixel Dimension unification → Pixel Frame → ROI Crop
  → STEP 3: Brightness Normalization (Histogram Matching)
  → STEP 4: Change Detection (Difference → Threshold → Morphology → Change Mask)
  → STEP 5: Region Extraction (Contour → Bounding Box → Summary)
  → STEP 6: Visualization (Before / After / Overlay / Comparison)
  → STEP 7: Report (report.pdf)
```

**STEP 3 — Brightness Normalization**: T1 is the baseline; T2's brightness is adjusted to match T1 via Histogram Matching. Output: `project/normalized/normalized_T1.png`, `normalized_T2.png`.

**STEP 4 — Change Detection**: `cv2.absdiff` on normalized T1/T2 → threshold → morphological opening/closing → change mask. Output: `project/change/difference.png`, `change_mask.png`.

**STEP 5 — Region Extraction**: contour detection on the change mask → small-area filtering → bounding boxes → per-region summary (pixel area + bounding box only; no m², no volume, no object classification in MVP). Output: `contours.json`, `summary.json`.

**STEP 6 — Visualization**: Before / After / Overlay (T1 + bounding boxes + change IDs) / side-by-side Comparison image. Output: `before.png`, `after.png`, `overlay.png`, `comparison.png`.

**STEP 7 — Report**: sales-facing PDF — project intro, Before, After, Change Overlay, Summary, manufacturing use-case scenario. Output: `report.pdf`.

**STEP 2 remaining sub-items** (Pixel Frame unification, Polygon ROI, Project Save/Load) are also part of "STEP 2 complete" per the v6.0 definition, but are **not implemented yet** in this codebase — see Section 9 for exact status.

---

## 11. Core Design Principles

**Baseline First**: T1 is always the baseline for a project. T1 = Baseline, T2/T3/T4/... = Comparison. T1 is **never transformed**; only later timepoints are transformed to T1's frame. (Already followed by the current `affine.py`/`warp_image()` direction: T2 → T1.)

**Reference Frame**: The end goal is not merely "images visually overlap" — all timepoints must ultimately share: same location, same coordinate reference, same pixel size (GSD), same image dimensions, same ROI. Currently, `warp_image()` only guarantees **same image dimensions** (pixel count) as T1; it does not yet guarantee same GSD/pixel size (see STEP 2-E conclusion in Section 9 — currently not needed for real data, but this is the eventual target if a future dataset needs it).

**Repeatability**: A project's Control Points, Affine Matrix, Pixel Frame, ROI Polygon, and Metadata should eventually be persisted so that T3/T4/T5 can reuse the same baseline without re-doing Control Point selection from scratch. As of STEP 2-F, `project_io.py` implements Save/Load for T1/T2 image paths, Control Points, and the Affine Matrix (see Section 9). Pixel Frame and ROI Polygon persistence are not yet part of `project.json` — they will need to be added once STEP 2's remaining sub-items (Pixel Frame unification, Polygon ROI) are implemented.

---

## 12. MVP Scope

**Must implement:**
GeoTIFF → PNG, Metadata storage, Control Point Alignment, Affine, Warp, GSD/Pixel Frame, Polygon ROI, Brightness Normalization, Change Mask, Region Extraction, Bounding Box, Summary, Overlay, Comparison.

**Explicitly out of scope for now:**
- AI/ML: YOLO, SAM, deep learning, object classification
- Spatial analysis: m² calculation, volume calculation, DSM, point cloud, 3D mesh
- Automation: auto feature matching (SIFT/ORB/ECC), real-time processing, Web GIS, automated LLM analysis

---

## 13. Dependencies

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

## 14. Important Development Rules

**Data & structure rules:**
- `projects/tif/` is **original source data** — never modify TIF files.
- PNG files are **derived** from TIF and may be regenerated/overwritten when re-running STEP 1.
- `projects/aligned/*.png` is generated output — do not treat as source data, but don't casually overwrite it during unrelated testing either.
- Preserve the current project layout (`projects/`, `src/align/` structure). Do not pre-create STEP 3–7 directories/files before actually implementing them.
- `__pycache__/`, `*.pyc`, `venv/` are excluded via `.gitignore` — do not commit build artifacts.

**Per-step protection rules:**
- Do not modify STEP 1 code while implementing STEP 2, and vice versa.
- Within STEP 2, `affine.py`'s `compute_affine()`/`warp_image()` are considered stable/verified — do not change their algorithm (e.g. switching to `estimateAffinePartial2D`, injecting GSD into the Affine calculation, or forcing matrix scale) without an explicit, separate request and re-verification.
- `control_points.py`, `polygon.py`, `project_io.py` should only be modified when the task explicitly targets them.

**Agent workflow rules (from v6.0 spec, applies to all coding agents on this project):**
1. Read the current code before making changes.
2. Identify the exact target file(s) to modify.
3. State a short plan before modifying, when the task is non-trivial.
4. Only implement after explicit user approval/request.
5. Preserve existing code structure as much as possible.
6. Avoid unnecessary refactoring.
7. Implement one feature per step/request.
8. Test after implementing, using real project data where possible.
9. Report changed files and test results clearly.
10. Do not ask a coding agent to implement multiple STEPs in a single request — analyze → confirm → minimal change → test → next step.

**Philosophy**: this is not a research image-processing project — it is the first product of a repeatable spatial-change-recording service. Priority order: (1) get the Baseline exactly right, (2) build a repeatable data structure, (3) make each step's input/output explicit, (4) make results human-understandable, (5) get in front of a real customer quickly. Do not over-invest in accuracy before the pipeline is repeatable and sellable.

---

## 15. Next Development Step

**STEP 1 is complete and verified.**
**STEP 2-A through STEP 2-F are complete and verified** (GUI, Control Points, Affine, Warp, Overlay + Opacity, GSD comparison/display, Project Save/Load). STEP 2-E is committed (`80a8eeb`); STEP 2-F (`project_io.py` + related `align_images.py` changes) is implemented and verified but **not yet committed**.

**Open decision points for the next step** (not yet decided by the user):
1. Commit STEP 2-F changes (`src/align/project_io.py`, `src/align/align_images.py`).
2. Within STEP 2, whether to implement Polygon ROI (`polygon.py`) next, or consider STEP 2 "done enough" and move to STEP 3 (Brightness Normalization).
3. If GSD differences are much larger in a future dataset, revisit whether explicit GSD Resampling (deferred in STEP 2-E) becomes necessary.
4. Decide whether Pixel Frame unification and ROI persistence should be added to `project.json`'s schema once those features exist (current `version: 1` schema only covers images/Control Points/Affine/aligned image).

Per the agent workflow rules in Section 14, the next actual implementation step should be scoped as a single, small, explicitly-requested task rather than inferred automatically from this document.
