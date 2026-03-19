#!/usr/bin/env python3
"""
Near-duplicate finder using perceptual hashing.
Outputs a list of files to remove before manual review.

Usage: python3 dedupe.py ~/dataset/sorted/accepted
"""
from imagededup.methods import PHash
from pathlib import Path
import json, sys, shutil

accepted_dir = Path(sys.argv[1])
dupes_dir = accepted_dir.parent / "duplicates"
dupes_dir.mkdir(exist_ok=True)

phasher = PHash()
encodings = phasher.encode_images(image_dir=str(accepted_dir))
duplicates = phasher.find_duplicates(encoding_map=encodings, max_distance_threshold=10)

removed = set()
for source, dupe_list in duplicates.items():
    for dupe in dupe_list:
        if dupe not in removed and source not in removed:
            dupe_path = accepted_dir / dupe
            if dupe_path.exists():
                shutil.move(str(dupe_path), dupes_dir / dupe)
                removed.add(dupe)

print(f"Moved {len(removed)} near-duplicates to {dupes_dir}")
