#!/usr/bin/env python3
"""
Generate data.json for the LoRA dataset gallery reviewer.
Each image gets one winning tag per axis group (if above threshold),
combined across all axes — so one image can be tagged with phstyle_strip
+ phdns_sparse + phlen_short + phtex_curly + lmaj_full + lmin_protruding + hood_covered.

Usage:
    python3 generate_data.py ~/dataset/clip_labels.json ~/dataset/data.json

Then serve from the dataset directory:
    cd ~/dataset && python3 -m http.server 8000
    open http://localhost:8000/gallery.html
"""

import json
import sys
from pathlib import Path
from collections import Counter

AXIS_GROUPS = {
    "style":   ["phstyle_bare", "phstyle_stubble", "phstyle_strip", "phstyle_trimmed", "phstyle_bush"],
    "density": ["phdns_sparse", "phdns_moderate", "phdns_thick"],
    "length":  ["phlen_stubble", "phlen_short", "phlen_medium", "phlen_long"],
    "texture": ["phtex_straight", "phtex_wavy", "phtex_curly", "phtex_coily"],
    "lmaj":    ["lmaj_flat", "lmaj_full"],
    "lmin":    ["lmin_tucked", "lmin_protruding"],
    "hood":    ["hood_covered", "hood_exposed"],
}

ALL_TAGS = [tag for group in AXIS_GROUPS.values() for tag in group]

# Minimum CLIP confidence for a tag to be assigned
THRESHOLD = 0.40


def assign_tags(scores: dict) -> list:
    """
    For each axis group, pick the highest-scoring tag if it clears THRESHOLD.
    Returns a list of tags — one per axis at most, potentially fewer if
    CLIP wasn't confident enough on some axes.
    """
    tags = []
    for group_tags in AXIS_GROUPS.values():
        group_scores = {t: scores.get(t, 0.0) for t in group_tags}
        best = max(group_scores, key=group_scores.get)
        if group_scores[best] >= THRESHOLD:
            tags.append(best)
    return tags


def main():
    if len(sys.argv) < 3:
        print("Usage: generate_data.py <clip_labels.json> <output/data.json>")
        sys.exit(1)

    labels_path = Path(sys.argv[1]).expanduser().resolve()
    out_path    = Path(sys.argv[2]).expanduser().resolve()
    base_dir    = out_path.parent  # paths in data.json are relative to this directory

    if not labels_path.exists():
        print(f"Error: {labels_path} not found")
        sys.exit(1)

    out_path.parent.mkdir(parents=True, exist_ok=True)

    with open(labels_path) as f:
        clip_results = json.load(f)

    images = []
    subreddits = set()

    for i, entry in enumerate(clip_results):
        abs_path = Path(entry["path"])
        try:
            rel_path = str(abs_path.relative_to(base_dir))
        except ValueError:
            # Path is outside base_dir — keep absolute, img src will break on server
            # but at least the data is there
            rel_path = str(abs_path)

        subreddit = entry.get("subreddit", "unknown")
        subreddits.add(subreddit)

        tags = assign_tags(entry.get("scores", {}))

        images.append({
            "id":          i,
            "path":        rel_path,
            "subreddit":   subreddit,
            "clip_scores": entry.get("scores", {}),
            "tags":        tags,
            "status":      "unreviewed",   # unreviewed | selected | rejected
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

    with open(out_path, "w") as f:
        json.dump(data, f, indent=2)

    print(f"\nWrote {out_path}")
    print(f"  {len(images)} images  |  {len(subreddits)} subreddits")

    tag_counts = Counter(tag for img in images for tag in img["tags"])
    print("\nTag distribution (bar = per 5 images):")
    current_axis = None
    for axis, axis_tags in AXIS_GROUPS.items():
        if axis != current_axis:
            print(f"\n  [{axis}]")
            current_axis = axis
        for tag in axis_tags:
            n   = tag_counts.get(tag, 0)
            bar = "█" * (n // 5) + ("▌" if n % 5 >= 3 else "")
            print(f"    {tag:30} {n:4}  {bar}")

    no_tags = sum(1 for img in images if not img["tags"])
    if no_tags:
        print(f"\n  Warning: {no_tags} images had no tags assigned (all scores below {THRESHOLD})")
        print("  Consider lowering THRESHOLD in the script if this is unexpected.")


if __name__ == "__main__":
    main()
