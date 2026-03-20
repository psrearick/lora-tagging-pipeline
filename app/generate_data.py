#!/usr/bin/env python3
"""
Generate or update data.json. Reads all axis/tag config from lora_config.json.

Usage:
    python3 generate_data.py clip_labels.json data.json
    python3 generate_data.py clip_labels.json data.json --update
    python3 generate_data.py clip_labels.json data.json --update --reclip
    python3 generate_data.py clip_labels.json data.json --config ~/dataset/lora_config.json
"""

import json
import sys
import argparse
from pathlib import Path
from collections import Counter
from config_loader import load_config


def assign_auto_tags(scores: dict, cfg) -> list:
    tags = []
    for axis_tags in cfg.axis_groups.values():
        group_scores = {t: scores.get(t, 0.0) for t in axis_tags}
        best = max(group_scores, key=group_scores.get)
        if group_scores[best] >= cfg.threshold:
            tags.append(best)
    return tags


def merge_tags(existing_tags: list, new_auto_tags: list, cfg) -> list:
    manual   = [t for t in existing_tags if t not in cfg.all_tags]
    return list(dict.fromkeys(new_auto_tags + manual))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("clip_labels", type=Path)
    parser.add_argument("output",      type=Path)
    parser.add_argument("--config",    type=Path, default="lora_config.json")
    parser.add_argument("--update",    action="store_true")
    parser.add_argument("--reclip",    action="store_true")
    args = parser.parse_args()

    cfg         = load_config(args.config)
    labels_path = args.clip_labels.expanduser().resolve()
    out_path    = args.output.expanduser().resolve()
    base_dir    = out_path.parent

    with open(labels_path) as f:
        clip_results = json.load(f)

    clip_by_path = {}
    for entry in clip_results:
        abs_path = Path(entry["path"])
        try:
            rel = str(abs_path.relative_to(base_dir))
        except ValueError:
            rel = str(abs_path)
        clip_by_path[rel] = entry

    if args.update and out_path.exists():
        print(f"Updating {out_path}...")
        with open(out_path) as f:
            data = json.load(f)

        # Refresh schema fields from config
        data["all_tags"]     = cfg.all_tags
        data["axis_groups"]  = cfg.axis_groups
        data["tag_synonyms"] = cfg.synonyms

        existing_subs = set(data.get("subreddits", []))
        for entry in clip_results:
            existing_subs.add(entry.get("subreddit", "unknown"))
        data["subreddits"] = sorted(existing_subs)

        existing_paths = {img["path"] for img in data["images"]}
        updated = added = skipped = 0

        for img in data["images"]:
            clip = clip_by_path.get(img["path"])
            if clip is None:
                skipped += 1
                continue
            img["clip_scores"] = clip.get("scores", img.get("clip_scores", {}))
            if args.reclip or "tags" not in img:
                new_auto   = assign_auto_tags(img["clip_scores"], cfg)
                img["tags"] = merge_tags(img.get("tags", []), new_auto, cfg)
                updated += 1

        max_id = max((img["id"] for img in data["images"]), default=-1)
        for rel_path, entry in clip_by_path.items():
            if rel_path in existing_paths:
                continue
            max_id += 1
            data["images"].append({
                "id":          max_id,
                "path":        rel_path,
                "subreddit":   entry.get("subreddit", "unknown"),
                "clip_scores": entry.get("scores", {}),
                "tags":        assign_auto_tags(entry.get("scores", {}), cfg),
                "status":      "unreviewed",
                "notes":       "",
            })
            added += 1

        print(f"  Updated: {updated}  Added: {added}  Skipped: {skipped}")

    else:
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
            images.append({
                "id":          i,
                "path":        rel_path,
                "subreddit":   subreddit,
                "clip_scores": entry.get("scores", {}),
                "tags":        assign_auto_tags(entry.get("scores", {}), cfg),
                "status":      "unreviewed",
                "notes":       "",
            })
        data = {
            "version":      1,
            "all_tags":     cfg.all_tags,
            "axis_groups":  cfg.axis_groups,
            "tag_synonyms": cfg.synonyms,
            "subreddits":   sorted(subreddits),
            "lastModified": 0,
            "images":       images,
        }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(data, f, indent=2)

    print(f"\nWrote {out_path}  ({len(data['images'])} images)")

    tag_counts = Counter(tag for img in data["images"] for tag in img["tags"])
    for axis, axis_tags in cfg.axis_groups.items():
        print(f"\n  [{axis}]")
        for tag in axis_tags:
            n   = tag_counts.get(tag, 0)
            bar = "█" * (n // 5)
            print(f"    {cfg.display_name(tag):30} ({tag})  {n:4}  {bar}")


if __name__ == "__main__":
    main()
