#!/usr/bin/env python3
"""
Export selected images as training data. Reads all config from lora_config.json.

Usage:
    python3 export_training.py data.json ~/dataset
    python3 export_training.py data.json ~/dataset --group-by-lora
    python3 export_training.py data.json ~/dataset --config ~/dataset/lora_config.json
"""

import os
import json
import argparse
from pathlib import Path
from PIL import Image
from config_loader import load_config


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("data_json",        type=Path)
    parser.add_argument("base_dir",         type=Path)
    parser.add_argument("--output_dir",     type=Path)
    parser.add_argument("--config",         type=Path)
    parser.add_argument("--group-by-lora",  action="store_true")
    parser.add_argument("--status",         nargs="+", default=["selected"])
    args = parser.parse_args()

    data_path = args.data_json.expanduser().resolve()
    if not os.path.exists(data_path):
        print(f"data_path not found: {data_path}")
        exit()

    base_dir  = args.base_dir.expanduser().resolve()
    if not os.path.exists(base_dir):
        print(f"base_dir not found: {base_dir}")
        exit()

    base_dir  = args.base_dir.expanduser().resolve()
    if not os.path.exists(base_dir):
        print(f"base_dir not found: {base_dir}")
        exit()

    config_path = args.config.expanduser().resolve() if args.config else base_dir / "lora_config.json"
    if not os.path.exists(config_path):
        print(f"config_path not found: {config_path}")
        exit()

    cfg       = load_config(config_path)
    out_dir   = args.output_dir.expanduser().resolve() if args.output_dir else base_dir / "training"

    with open(data_path) as f:
        data = json.load(f)

    exportable = [img for img in data.get("images", []) if img.get("status") in args.status]

    print(f"Project        : {cfg.project_name}")
    print(f"Exporting      : {len(exportable)} images")
    print(f"Group by LoRA  : {'yes' if args.group_by_lora else 'no'}")
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
        caption = cfg.make_caption(tags)
        stem    = src.stem

        dest_dirs = (
            [out_dir / lora for lora in cfg.all_loras_for_tags(tags)]
            if args.group_by_lora
            else [out_dir]
        )

        try:
            pil_img = Image.open(src).convert("RGB")
            for dest_dir in dest_dirs:
                dest_dir.mkdir(parents=True, exist_ok=True)
                pil_img.save(dest_dir / f"{stem}.png", "PNG")
                (dest_dir / f"{stem}.txt").write_text(caption, encoding="utf-8")
                lora_counts[dest_dir.name] = lora_counts.get(dest_dir.name, 0) + 1
            exported += 1
            if exported % 50 == 0:
                print(f"  {exported}/{len(exportable)}...")
        except Exception as e:
            print(f"  ERROR {src.name}: {e}")
            errors += 1

    print(f"\nExported : {exported}")
    print(f"Skipped  : {skipped}")
    print(f"Errors   : {errors}")
    if lora_counts:
        print("\nBy folder:")
        for folder, count in sorted(lora_counts.items()):
            print(f"  {folder:35} {count}")


if __name__ == "__main__":
    main()
