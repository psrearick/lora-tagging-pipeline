#!/usr/bin/env python3
"""
Export selected images from data.json into a training directory.
Writes image files + .txt caption sidecars in kohya/AI Toolkit format.

Usage:
    # Basic export — copies images as-is, writes captions
    python3 export_training.py ~/dataset/data.json ~/dataset/training

    # Export grouped into subdirs by primary axis (one folder per LoRA)
    python3 export_training.py ~/dataset/data.json ~/dataset/training --group-by-lora

    # Export only specific statuses (default: selected only)
    python3 export_training.py ~/dataset/data.json ~/dataset/training --status selected reviewed
"""

import json
import shutil
import argparse
import cv2
import numpy as np
from pathlib import Path
from PIL import Image

# Maps each tag to which LoRA it primarily trains.
# Images get placed in the folder of whichever LoRA their first style/anatomy
# tag belongs to. Change grouping logic below if you want different behavior.
TAG_TO_LORA = {}
LORA_AXES = {
    "lora1_style_density": ["style", "density"],
    "lora2_length":        ["length"],
    "lora3_texture":       ["texture"],
    "lora4_anatomy":       ["lmaj", "lmin", "hood"],
    "lora5_pose":          ["position", "interaction"],
}


def build_tag_lora_map(axis_groups: dict):
    """Build reverse lookup: tag → lora name, based on which axes each LoRA owns."""
    for lora_name, axes in LORA_AXES.items():
        for axis in axes:
            for tag in axis_groups.get(axis, []):
                TAG_TO_LORA[tag] = lora_name


def primary_lora(tags: list) -> str:
    """Return the LoRA folder name for this image based on its first recognizable tag."""
    for tag in tags:
        if tag in TAG_TO_LORA:
            return TAG_TO_LORA[tag]
    return "unassigned"


def make_caption(tags: list) -> str:
    """
    Comma-separated tag list for the .txt sidecar.
    AI Toolkit and kohya both expect this format.
    Order: style first, then density, length, texture, anatomy, pose — readable left to right.
    """
    return ", ".join(tags)


def copy_as_is(src: Path) -> Image.Image:
    return Image.open(src).convert("RGB")


def main():
    parser = argparse.ArgumentParser(description="Export training dataset from data.json")
    parser.add_argument("data_json",   type=Path, help="data.json from gallery reviewer")
    parser.add_argument("output_dir",  type=Path, help="Training output directory")
    parser.add_argument("--group-by-lora", action="store_true",
                        help="Place images in subdirectories by LoRA assignment")
    parser.add_argument("--status",    nargs="+", default=["selected"],
                        help="Which status values to export (default: selected)")
    args = parser.parse_args()

    data_path  = args.data_json.expanduser().resolve()
    out_dir    = args.output_dir.expanduser().resolve()
    base_dir   = data_path.parent

    with open(data_path) as f:
        data = json.load(f)

    build_tag_lora_map(data.get("axis_groups", {}))

    images     = data.get("images", [])
    exportable = [img for img in images if img.get("status") in args.status]

    print(f"Total images in data.json: {len(images)}")
    print(f"Exporting ({', '.join(args.status)}): {len(exportable)}")
    print(f"Output: {out_dir}")
    print(f"Group by LoRA: {'yes' if args.group_by_lora else 'no — flat'}")
    print()

    out_dir.mkdir(parents=True, exist_ok=True)

    exported = skipped = errors = 0
    lora_counts = {}

    for img in exportable:
        src = base_dir / img["path"]
        if not src.exists():
            print(f"  SKIP (missing): {img['path']}")
            skipped += 1
            continue

        tags    = img.get("tags", [])
        caption = make_caption(tags)

        # Determine output subdirectory
        if args.group_by_lora:
            lora = primary_lora(tags)
            dest_dir = out_dir / lora
        else:
            dest_dir = out_dir

        dest_dir.mkdir(parents=True, exist_ok=True)

        # Build output filename — strip subreddit prefix noise, keep id
        stem    = src.stem
        img_out = dest_dir / f"{stem}.png"   # always write PNG — lossless
        txt_out = dest_dir / f"{stem}.txt"

        try:
            pil_img = copy_as_is(src)

            pil_img.save(img_out, "PNG")
            txt_out.write_text(caption, encoding="utf-8")

            lora_name = primary_lora(tags) if args.group_by_lora else "flat"
            lora_counts[lora_name] = lora_counts.get(lora_name, 0) + 1
            exported += 1

            if exported % 50 == 0:
                print(f"  {exported}/{len(exportable)} exported...")

        except Exception as e:
            print(f"  ERROR on {src.name}: {e}")
            errors += 1

    print(f"\n{'─'*40}")
    print(f"Exported : {exported}")
    print(f"Skipped  : {skipped}")
    print(f"Errors   : {errors}")

    if lora_counts:
        print("\nBy folder:")
        for lora, count in sorted(lora_counts.items()):
            print(f"  {lora:35} {count}")

    print(f"\nCaption format sample:")
    sample = next((i for i in exportable if i.get("tags")), None)
    if sample:
        print(f"  {make_caption(sample['tags'])}")


if __name__ == "__main__":
    main()
