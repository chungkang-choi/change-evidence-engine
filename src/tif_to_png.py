#!/usr/bin/env python3
"""Convert a single TIF/TIFF image to PNG (first IFD / frame 0 only).

Dependency: pip install pillow

Usage:
  python src/tif_to_png.py <input> [output]

If output is omitted, writes <input_stem>.png beside the input.
Existing PNG at the output path is overwritten without prompting.
Only the first IFD / frame is converted; overview IFDs are ignored.
GeoTIFF georeferencing is discarded.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image, UnidentifiedImageError

# Modes Pillow can write to PNG without conversion.
_PNG_SAFE_MODES = frozenset(
    {"1", "L", "LA", "I", "P", "RGB", "RGBA", "RGBX"}
)


def _png_safe(image: Image.Image) -> Image.Image:
    """Return an image in a mode suitable for PNG save.

    Preserve PNG-compatible modes. Convert only when save requires it.
    Prefer RGB when no alpha, RGBA when alpha is present.
    """
    if image.mode in _PNG_SAFE_MODES:
        return image
    if image.mode in {"RGBa", "LA"} or "A" in image.getbands():
        return image.convert("RGBA")
    return image.convert("RGB")


def convert(input_path: Path, output_path: Path) -> None:
    """Open input TIFF (frame 0), write PNG to output_path.

    Raises:
        FileNotFoundError: input missing, or output parent directory missing.
        IsADirectoryError: input path is a directory.
        ValueError: output path equals input path.
        UnidentifiedImageError / OSError: unreadable or non-image input,
            or save failure.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input not found: {input_path}")
    if input_path.is_dir():
        raise IsADirectoryError(f"Input is a directory: {input_path}")

    if output_path.resolve() == input_path.resolve():
        raise ValueError("Output path must differ from input path")

    parent = output_path.parent
    if not parent.exists():
        raise FileNotFoundError(f"Output directory does not exist: {parent}")
    if not parent.is_dir():
        raise NotADirectoryError(f"Output parent is not a directory: {parent}")

    with Image.open(input_path) as img:
        # First IFD / frame 0 only; ignore overview IFDs.
        try:
            img.seek(0)
        except EOFError:
            pass
        frame = img.copy()

    frame = _png_safe(frame)
    frame.save(output_path, format="PNG")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Convert one TIF/TIFF image file to one PNG. "
            "Uses the first IFD / frame only (overview IFDs ignored). "
            "Existing output PNG is overwritten without prompting."
        ),
        epilog=(
            "Dependency: pip install pillow. "
            "Accepts paths Pillow can open as TIFF (.tif/.tiff suggested)."
        ),
    )
    parser.add_argument(
        "input",
        type=Path,
        help="Path to a TIFF image (.tif / .tiff)",
    )
    parser.add_argument(
        "output",
        type=Path,
        nargs="?",
        default=None,
        help=(
            "Output PNG path (default: <input_stem>.png beside the input; "
            "overwrites without prompting)"
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    input_path = args.input
    if args.output is None:
        output_path = input_path.with_suffix(".png")
    else:
        output_path = args.output

    try:
        convert(input_path, output_path)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except IsADirectoryError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except NotADirectoryError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except PermissionError as exc:
        print(f"Permission denied: {exc}", file=sys.stderr)
        return 1
    except UnidentifiedImageError:
        print(f"Not a readable image: {input_path}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"Failed to convert: {exc}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(output_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
