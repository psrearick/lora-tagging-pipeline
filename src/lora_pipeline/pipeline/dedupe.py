#!/usr/bin/env python3
"""
PHash deduplicator — no imagededup dependency, no multiprocessing drama.
Usage: python3 dedupe.py ~/dataset/sorted/accepted
"""
import sys, shutil
from pathlib import Path
from PIL import Image
import numpy as np

IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.webp'}
HASH_SIZE   = 8
MAX_HAMMING = 10   # images within this distance are considered near-duplicates


def phash(img_path: Path) -> int|None:
    try:
        img  = Image.open(img_path).convert('L').resize(
            (HASH_SIZE * 4, HASH_SIZE * 4), Image.LANCZOS # type: ignore
        )
        arr  = np.array(img, dtype=float)
        # DCT via cosine transform approximation — fast and dependency-free
        dct  = np.fft.rfft2(arr)
        dct  = np.abs(dct[:HASH_SIZE, :HASH_SIZE])
        med  = np.median(dct)
        bits = (dct > med).flatten()
        # Pack 64 bits into a single int for fast hamming distance
        val  = 0
        for b in bits:
            val = (val << 1) | int(b)
        return val
    except Exception:
        return None


def hamming(a: int, b: int) -> int:
    return bin(a ^ b).count('1')


def run(accepted_dir: Path) -> int:
    dupes_dir = accepted_dir.parent / 'duplicates'
    dupes_dir.mkdir(exist_ok=True)

    print("Hashing images...")
    images = [p for p in accepted_dir.rglob('*') if p.suffix.lower() in IMAGE_EXTS]
    hashes = {}
    for i, p in enumerate(images):
        h = phash(p)
        if h is not None:
            hashes[p] = h
        if i % 100 == 0:
            print(f"  {i}/{len(images)}")

    print(f"Comparing {len(hashes)} hashes...")
    paths  = list(hashes.keys())
    removed = set()

    for i in range(len(paths)):
        if paths[i] in removed:
            continue
        for j in range(i + 1, len(paths)):
            if paths[j] in removed:
                continue
            if hamming(hashes[paths[i]], hashes[paths[j]]) <= MAX_HAMMING:
                dest = dupes_dir / paths[j].name
                shutil.move(str(paths[j]), dest)
                removed.add(paths[j])

    print(f"Moved {len(removed)} near-duplicates to {dupes_dir}")
    return len(removed)


if __name__ == '__main__':
    accepted_dir = Path(sys.argv[1]).expanduser().resolve()
    run(accepted_dir)
