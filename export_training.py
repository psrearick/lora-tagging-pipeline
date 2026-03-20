#!/usr/bin/env python3
"""
Export selected images from data.json into training directories.
Writes image files + .txt caption sidecars in kohya/AI Toolkit format.

Usage:
    # Flat output — all selected images in one directory
    python3 export_training.py ~/dataset/data.json ~/dataset/training

    # Grouped by LoRA — each image copied into every LoRA dir it belongs to
    python3 export_training.py ~/dataset/data.json ~/dataset/training --group-by-lora

    # Export specific statuses (default: selected only)
    python3 export_training.py ~/dataset/data.json ~/dataset/training --status selected reviewed
"""

import json
import argparse
import shutil
from pathlib import Path
from PIL import Image

# Maps axis group names to LoRA folder names.
# An image tagged with tags from multiple axes lands in multiple folders.
LORA_AXES = {
    "lora1_style_density": ["style", "density"],
    "lora2_length":        ["length"],
    "lora3_texture":       ["texture"],
    "lora4_anatomy":       ["lmaj", "lmin", "hood"],
    "lora5_pose":          ["position", "interaction"],
}

# Synonym map — each tag expands to natural language aliases.
# All aliases land in the caption file, comma separated.
# Tag shuffle in AI Toolkit randomizes which ones the model sees each step.
SYNONYMS = {
    # Style
    "phstyle_bare":       ["bare", "shaved", "smooth", "fully shaved", "no pubic hair"],
    "phstyle_stubble":    ["stubble", "shaved stubble", "razor stubble", "regrowth"],
    "phstyle_strip":      ["landing strip", "vertical strip", "narrow strip"],
    "phstyle_trimmed":    ["trimmed", "neatly trimmed", "shaped pubic hair"],
    "phstyle_bush":       ["bush", "full bush", "natural pubic hair", "unshaved", "untrimmed"],
    # Density
    "phdns_sparse":       ["sparse pubic hair", "thin pubic hair", "light pubic hair"],
    "phdns_moderate":     ["moderate pubic hair", "medium pubic hair"],
    "phdns_thick":        ["thick pubic hair", "dense pubic hair", "full pubic hair"],
    # Length
    "phlen_stubble":      ["very short pubic hair", "close cropped pubic hair"],
    "phlen_short":        ["short pubic hair", "cropped pubic hair"],
    "phlen_medium":       ["medium length pubic hair"],
    "phlen_long":         ["long pubic hair"],
    # Texture
    "phtex_straight":     ["straight pubic hair"],
    "phtex_wavy":         ["wavy pubic hair"],
    "phtex_curly":        ["curly pubic hair"],
    "phtex_coily":        ["coily pubic hair", "kinky pubic hair", "tightly coiled pubic hair"],
    # Anatomy
    "lmaj_flat":          ["flat labia", "minimal labia majora"],
    "lmaj_full":          ["full labia", "prominent labia majora", "large labia majora"],
    "lmin_tucked":        ["tucked labia minora", "inner labia not visible"],
    "lmin_protruding":    ["protruding labia minora", "visible inner labia",
                           "labia minora visible", "extended inner labia"],
    "hood_covered":       ["covered clitoral hood", "clitoris covered"],
    "hood_exposed":       ["exposed clitoris", "visible clitoris", "retracted clitoral hood"],
    # Position
    "pos_standing":       ["standing", "standing upright"],
    "pos_sitting":        ["sitting", "seated"],
    "pos_kneeling":       ["kneeling"],
    "pos_lying_back":     ["lying on back", "on her back", "supine"],
    "pos_lying_side":     ["lying on side", "on her side"],
    "pos_all_fours":      ["on all fours", "on hands and knees", "doggy position"],
    "pos_squatting":      ["squatting", "legs spread squatting"],
    # Interaction
    "int_natural":        ["hands away", "no touching"],
    "int_spreading":      ["spreading", "spreading labia", "fingers spreading",
                           "holding open", "spread open"],
    "int_touching":       ["touching", "self touching", "fingering"],
    "int_toy":            ["using toy", "sex toy", "vibrator", "toy inserted"],
}


# Populated at runtime from data.json axis_groups + LORA_AXES
TAG_TO_LORA = {}


def build_tag_lora_map(axis_groups: dict):
    """Reverse lookup: tag → lora folder name."""
    for lora_name, axes in LORA_AXES.items():
        for axis in axes:
            for tag in axis_groups.get(axis, []):
                TAG_TO_LORA[tag] = lora_name


def all_loras(tags: list) -> list:
    """
    Return every LoRA folder this image belongs to.
    One image with tags spanning multiple axes lands in multiple folders —
    that's correct and intentional. Each LoRA sees only images relevant to it.
    """
    matched = set()
    for tag in tags:
        if tag in TAG_TO_LORA:
            matched.add(TAG_TO_LORA[tag])
    return sorted(matched) if matched else ["unassigned"]


def make_caption(tags: list) -> str:
    """
    Expand each tag into its natural language synonyms.
    All synonyms land in the caption — AI Toolkit's tag shuffle
    randomizes which subset the model sees each training step,
    teaching the semantic neighborhood rather than one fixed token.
    """
    terms = []
    for tag in tags:
        terms.extend(SYNONYMS.get(tag, [tag]))  # fallback to raw tag if no synonyms defined
    return ", ".join(terms)


def copy_image(src: Path, dest: Path):
    """
    Copy image to destination, converting to PNG if not already.
    PNG is lossless and universally accepted by training tools.
    """
    if src.suffix.lower() == ".png":
        shutil.copy2(src, dest)
    else:
        img = Image.open(src).convert("RGB")
        img.save(dest, "PNG")


def main():
    parser = argparse.ArgumentParser(description="Export training dataset from data.json")
    parser.add_argument("data_json",       type=Path,
                        help="data.json from gallery reviewer")
    parser.add_argument("output_dir",      type=Path,
                        help="Root training output directory")
    parser.add_argument("--group-by-lora", action="store_true",
                        help="Place images in subdirectories by LoRA assignment. "
                             "Images belonging to multiple LoRAs are copied into each.")
    parser.add_argument("--status",        nargs="+", default=["selected"],
                        help="Which status values to export (default: selected)")
    args = parser.parse_args()

    data_path = args.data_json.expanduser().resolve()
    out_dir   = args.output_dir.expanduser().resolve()
    base_dir  = data_path.parent

    if not data_path.exists():
        print(f"Error: {data_path} not found")
        raise SystemExit(1)

    with open(data_path) as f:
        data = json.load(f)

    build_tag_lora_map(data.get("axis_groups", {}))

    images     = data.get("images", [])
    exportable = [img for img in images if img.get("status") in args.status]

    print(f"Total images in data.json : {len(images)}")
    print(f"Statuses being exported   : {', '.join(args.status)}")
    print(f"Images to export          : {len(exportable)}")
    print(f"Output root               : {out_dir}")
    print(f"Group by LoRA             : {'yes' if args.group_by_lora else 'no — flat'}")
    print()

    out_dir.mkdir(parents=True, exist_ok=True)

    exported    = 0
    skipped     = 0
    errors      = 0
    lora_counts = {}

    for img in exportable:
        src = base_dir / img["path"]

        if not src.exists():
            print(f"  SKIP (missing): {img['path']}")
            skipped += 1
            continue

        tags    = img.get("tags", [])
        caption = make_caption(tags)
        stem    = src.stem

        dest_dirs = (
            [out_dir / lora for lora in all_loras(tags)]
            if args.group_by_lora
            else [out_dir]
        )

        try:
            # Load once, write to every applicable LoRA directory
            pil_img = Image.open(src).convert("RGB")
            wrote   = False

            for dest_dir in dest_dirs:
                dest_dir.mkdir(parents=True, exist_ok=True)

                img_out = dest_dir / f"{stem}.png"
                txt_out = dest_dir / f"{stem}.txt"

                pil_img.save(img_out, "PNG")
                txt_out.write_text(caption, encoding="utf-8")

                folder = dest_dir.name
                lora_counts[folder] = lora_counts.get(folder, 0) + 1
                wrote = True

            if wrote:
                exported += 1

            if exported % 50 == 0:
                print(f"  {exported}/{len(exportable)} exported...")

        except Exception as e:
            print(f"  ERROR on {src.name}: {e}")
            errors += 1

    # ── Summary ────────────────────────────────────────────────────────────────
    print(f"\n{'─' * 44}")
    print(f"  Exported : {exported}")
    print(f"  Skipped  : {skipped}  (source file missing)")
    print(f"  Errors   : {errors}")

    if lora_counts:
        print(f"\n  Images per folder:")
        for folder, count in sorted(lora_counts.items()):
            bar = "█" * (count // 10)
            print(f"    {folder:35} {count:4}  {bar}")

    if exportable:
        sample = next((i for i in exportable if i.get("tags")), None)
        if sample:
            print(f"\n  Caption sample:")
            print(f"    {make_caption(sample['tags'])}")

    print()


if __name__ == "__main__":
    main()
