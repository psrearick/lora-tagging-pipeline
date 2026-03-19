#!/usr/bin/env python3
"""
Reorganize accepted images from subreddit subfolders into bucket subfolders
based on CLIP top_bucket assignment. Preserves subreddit name in filename prefix.

Usage: python3 reorganize_by_bucket.py ~/dataset/clip_labels.json ~/dataset/by_bucket
"""
import json, sys, shutil
from pathlib import Path

labels_path = Path(sys.argv[1])
out_dir = Path(sys.argv[2])

with open(labels_path) as f:
    results = json.load(f)

moved = 0
skipped = 0

for entry in results:
    src = Path(entry["path"])
    if not src.exists():
        skipped += 1
        continue

    bucket = entry["top_bucket"]
    subreddit = entry["subreddit"]
    score = entry["top_score"]

    dest_dir = out_dir / bucket
    dest_dir.mkdir(parents=True, exist_ok=True)

    # Prefix with subreddit + confidence so source stays traceable
    new_name = f"{subreddit}_{score:.3f}_{src.name}"
    dest = dest_dir / new_name

    shutil.copy2(src, dest)
    moved += 1

print(f"Organized {moved} images into {out_dir}")
print(f"Skipped {skipped} missing files")

# Print bucket counts
from collections import Counter
counts = Counter(e["top_bucket"] for e in results if Path(e["path"]).exists())
print("\nBucket counts:")
for bucket, count in sorted(counts.items()):
    print(f"  {bucket:30}: {count}")
