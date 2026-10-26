"""Build photos.json from the images in photos/.

Reads GPS coordinates from each photo's EXIF data and merges in the hints
from hints.json. Photos that are new get a blank entry in hints.json so
they're easy to fill in.

hints.json maps filename -> hint, or filename -> object to also fix a position:
    "IMG_0759.JPEG": "Jul 2022"
    "IMG_1560.JPEG": { "hint": "Jan 2024", "lat": 60.8409, "lng": 9.1701 }

Run from the repo root: python scripts/build_photos.py
Runs automatically on GitHub when photos/ or hints.json changes.
"""

import json
import sys
from pathlib import Path
from urllib.parse import quote

from PIL import ExifTags, Image

ROOT = Path(__file__).resolve().parent.parent
PHOTOS_DIR = ROOT / "photos"
HINTS_FILE = ROOT / "hints.json"
OUTPUT_FILE = ROOT / "photos.json"

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}
UNSUPPORTED_EXTS = {".heic", ".heif"}


def to_degrees(dms, ref):
    deg = float(dms[0]) + float(dms[1]) / 60 + float(dms[2]) / 3600
    return -deg if ref in ("S", "W") else deg


def read_gps(path):
    try:
        with Image.open(path) as img:
            gps = img.getexif().get_ifd(ExifTags.IFD.GPSInfo)
    except Exception as e:
        return None, f"could not read file ({e})"
    # GPS tags: 1 = lat ref, 2 = lat, 3 = lng ref, 4 = lng
    if not all(k in gps for k in (1, 2, 3, 4)):
        return None, "no GPS data in photo"
    try:
        lat = to_degrees(gps[2], gps[1])
        lng = to_degrees(gps[4], gps[3])
    except (TypeError, ValueError, ZeroDivisionError, IndexError):
        return None, "GPS data is malformed"
    if lat == 0 and lng == 0:
        return None, "GPS data is empty (0, 0)"
    return (round(lat, 6), round(lng, 6)), None


def main():
    hints = json.loads(HINTS_FILE.read_text(encoding="utf-8")) if HINTS_FILE.exists() else {}

    photos, skipped = [], []
    files = sorted(p for p in PHOTOS_DIR.iterdir() if p.is_file())

    for path in files:
        ext = path.suffix.lower()
        if ext in UNSUPPORTED_EXTS:
            skipped.append((path.name, "HEIC isn't shown by most browsers, convert to JPEG"))
            continue
        if ext not in IMAGE_EXTS:
            continue

        entry = hints.get(path.name, "")
        if isinstance(entry, str):
            entry = {"hint": entry}

        if "lat" in entry and "lng" in entry:
            coords = (entry["lat"], entry["lng"])
        else:
            coords, reason = read_gps(path)
            if coords is None:
                skipped.append((path.name, reason + ' (add "lat"/"lng" in hints.json to include it)'))
                continue

        photos.append({
            "url": "photos/" + quote(path.name),
            "lat": coords[0],
            "lng": coords[1],
            "hint": entry.get("hint", ""),
        })

        if path.name not in hints:
            hints[path.name] = ""

    OUTPUT_FILE.write_text(json.dumps(photos, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    HINTS_FILE.write_text(json.dumps(hints, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"photos.json: {len(photos)} photos")
    missing_hints = [p["url"] for p in photos if not p["hint"]]
    if missing_hints:
        print(f"{len(missing_hints)} without a hint (fill in hints.json):")
        for url in missing_hints:
            print(f"  - {url}")
    if skipped:
        print(f"Skipped {len(skipped)}:")
        for name, reason in skipped:
            print(f"  - {name}: {reason}")
        # Show as a warning annotation in the GitHub Actions summary
        for name, reason in skipped:
            print(f"::warning title=Photo skipped::{name}: {reason}", file=sys.stderr)


if __name__ == "__main__":
    main()
