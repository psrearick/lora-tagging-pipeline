#!/usr/bin/env python3
"""
Generate or update data.json for the LoRA dataset gallery reviewer.

Usage:
    # First run — generate fresh
    python3 generate_data.py ~/dataset/clip_labels.json ~/dataset/data.json

    # Update existing data.json with new axis groups / new images
    python3 generate_data.py ~/dataset/clip_labels.json ~/dataset/data.json --update

    # Update and also wipe auto-tags (keep manual + status, re-score everything)
    python3 generate_data.py ~/dataset/clip_labels.json ~/dataset/data.json --update --reclip
"""

import json
import sys
import argparse
from pathlib import Path
from collections import Counter

AXIS_GROUPS = {
    # LoRA 1 — Style + Density
    "style":    ["phstyle_bare", "phstyle_stubble", "phstyle_strip", "phstyle_trimmed", "phstyle_bush"],
    "density":  ["phdns_sparse", "phdns_moderate", "phdns_thick"],
    # LoRA 2 — Length
    "length":   ["phlen_stubble", "phlen_short", "phlen_medium", "phlen_long"],
    # LoRA 3 — Texture
    "texture":  ["phtex_straight", "phtex_wavy", "phtex_curly", "phtex_coily"],
    # LoRA 4 — Anatomy
    "lmaj":     ["lmaj_flat", "lmaj_full"],
    "lmin":     ["lmin_tucked", "lmin_protruding"],
    "hood":     ["hood_covered", "hood_exposed"],
    # LoRA 5 — Position
    "position": ["pos_standing", "pos_sitting", "pos_kneeling",
                 "pos_lying_back", "pos_lying_side", "pos_all_fours", "pos_squatting"],
    # LoRA 5 — Interaction
    "interaction": ["int_natural", "int_spreading", "int_touching", "int_toy"],
}

ALL_TAGS = [tag for group in AXIS_GROUPS.values() for tag in group]

THRESHOLD = 0.25


def assign_auto_tags(scores: dict) -> list:
    """Pick best tag per axis from stored CLIP scores if above threshold."""
    tags = []
    for group_tags in AXIS_GROUPS.values():
        group_scores = {t: scores.get(t, 0.0) for t in group_tags}
        best = max(group_scores, key=group_scores.get)
        if group_scores[best] >= THRESHOLD:
            tags.append(best)
    return tags


def is_auto_tag(tag: str) -> bool:
    """True if this tag is one the system assigns — vs. manually added."""
    return tag in ALL_TAGS


def merge_tags(existing_tags: list, new_auto_tags: list) -> list:
    """
    Keep manually-added tags (not in ALL_TAGS) always.
    Replace auto-tags with freshly computed ones.
    """
    manual = [t for t in existing_tags if not is_auto_tag(t)]
    return list(dict.fromkeys(new_auto_tags + manual))  # dedupe, preserve order


def load_existing(data_path: Path) -> dict:
    with open(data_path) as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(description="Generate or update LoRA review data.json")
    parser.add_argument("clip_labels", type=Path, help="clip_labels.json from clip_label.py")
    parser.add_argument("output",      type=Path, help="data.json to create or update")
    parser.add_argument("--update",    action="store_true",
                        help="Update existing data.json instead of overwriting")
    parser.add_argument("--reclip",    action="store_true",
                        help="With --update: re-evaluate auto-tags from stored CLIP scores "
                             "(keeps status and manual tags, replaces auto-tags)")
    args = parser.parse_args()

    labels_path = args.clip_labels.expanduser().resolve()
    out_path    = args.output.expanduser().resolve()
    base_dir    = out_path.parent

    if not labels_path.exists():
        print(f"Error: {labels_path} not found"); sys.exit(1)

    with open(labels_path) as f:
        clip_results = json.load(f)

    # Index clip results by relative path for fast lookup
    clip_by_path = {}
    for entry in clip_results:
        abs_path = Path(entry["path"])
        try:
            rel = str(abs_path.relative_to(base_dir))
        except ValueError:
            rel = str(abs_path)
        clip_by_path[rel] = entry

    # ── UPDATE MODE ────────────────────────────────────────────────────────────
    if args.update and out_path.exists():
        print(f"Updating existing {out_path}...")
        data = load_existing(out_path)

        # Update schema-level fields — never touch per-image review state
        data["all_tags"]    = ALL_TAGS
        data["axis_groups"] = AXIS_GROUPS

        # Add any subreddits from new clip results
        existing_subs = set(data.get("subreddits", []))
        for entry in clip_results:
            existing_subs.add(entry.get("subreddit", "unknown"))
        data["subreddits"] = sorted(existing_subs)

        # Track existing image paths to detect new arrivals
        existing_paths = {img["path"] for img in data["images"]}

        updated = added = skipped = 0

        # Update existing images
        for img in data["images"]:
            clip = clip_by_path.get(img["path"])
            if clip is None:
                # Image gone from clip results — leave it alone
                skipped += 1
                continue

            # Always refresh clip_scores in case clip was re-run
            img["clip_scores"] = clip.get("scores", img.get("clip_scores", {}))

            if args.reclip or "tags" not in img:
                # Re-derive auto tags from stored scores, preserve manual ones
                new_auto = assign_auto_tags(img["clip_scores"])
                img["tags"] = merge_tags(img.get("tags", []), new_auto)
                updated += 1

        # Add new images that aren't in existing data
        max_id = max((img["id"] for img in data["images"]), default=-1)
        for rel_path, entry in clip_by_path.items():
            if rel_path in existing_paths:
                continue
            max_id += 1
            auto_tags = assign_auto_tags(entry.get("scores", {}))
            data["images"].append({
                "id":          max_id,
                "path":        rel_path,
                "subreddit":   entry.get("subreddit", "unknown"),
                "clip_scores": entry.get("scores", {}),
                "tags":        auto_tags,
                "status":      "unreviewed",
                "notes":       "",
            })
            added += 1

        print(f"  Updated auto-tags: {updated}")
        print(f"  New images added:  {added}")
        print(f"  Skipped (no clip): {skipped}")

    # ── FRESH GENERATE ─────────────────────────────────────────────────────────
    else:
        if args.update:
            print(f"No existing data.json found at {out_path} — generating fresh.")

        images     = []
        subreddits = set()

        for i, entry in enumerate(clip_results):
            abs_path = Path(entry["path"])
            try:
                rel_path = str(abs_path.relative_to(base_dir))
            except ValueError:
                rel_path = str(abs_path)

            subreddit = entry.get("subreddit", "unknown")
            subreddits.add(subreddit)
            tags = assign_auto_tags(entry.get("scores", {}))

            images.append({
                "id":          i,
                "path":        rel_path,
                "subreddit":   subreddit,
                "clip_scores": entry.get("scores", {}),
                "tags":        tags,
                "status":      "unreviewed",
                "notes":       "",
            })

        data = {
            "version":      1,
            "all_tags":     ALL_TAGS,
            "axis_groups":  AXIS_GROUPS,
            "subreddits":   sorted(subreddits),
            "lastModified": 0,
            "images":       images,
        }

    # ── WRITE ──────────────────────────────────────────────────────────────────
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(data, f, indent=2)

    total = len(data["images"])
    print(f"\nWrote {out_path}  ({total} images)")

    tag_counts = Counter(tag for img in data["images"] for tag in img["tags"])
    print("\nTag distribution:")
    for axis, axis_tags in AXIS_GROUPS.items():
        print(f"\n  [{axis}]")
        for tag in axis_tags:
            n   = tag_counts.get(tag, 0)
            bar = "█" * (n // 5) + ("▌" if n % 5 >= 3 else "")
            print(f"    {tag:30} {n:4}  {bar}")

    no_tags = sum(1 for img in data["images"] if not img["tags"])
    if no_tags:
        print(f"\n  Warning: {no_tags} images had no tags assigned (all scores below {THRESHOLD})")


if __name__ == "__main__":
    main()
