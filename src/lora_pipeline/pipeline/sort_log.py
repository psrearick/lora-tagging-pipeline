#!/usr/bin/env python3
"""
Sort filter_log.jsonl by sharpness descending, output ranked file list per bucket.
Usage: python3 sort_log.py ~/dataset/sorted/filter_log.jsonl
"""
import json, sys
from pathlib import Path
from collections import defaultdict


def run(log_path: Path) -> None:
    buckets = defaultdict(list)

    with open(log_path) as f:
        for line in f:
            entry = json.loads(line)
            if entry["verdict"] == "accepted":
                buckets[entry["bucket"]].append(entry)

    for bucket, images in sorted(buckets.items()):
        ranked = sorted(images, key=lambda x: x["sharpness"], reverse=True)
        print(f"\n=== {bucket} ({len(ranked)} images) ===")
        for img in ranked[:5]:
            print(f"  {img['sharpness']:.1f}  {img['path']}")


if __name__ == '__main__':
    run(Path(sys.argv[1]))
