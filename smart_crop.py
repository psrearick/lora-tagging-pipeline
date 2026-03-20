#!/usr/bin/env python3
"""
Smart crop — resize shortest side to target, saliency-detect focal point,
crop target×target centered on it. Runs before CLIP labeling.

Usage:
    python3 smart_crop.py ~/dataset/sorted/accepted ~/dataset/cropped
    python3 smart_crop.py ~/dataset/sorted/accepted ~/dataset/cropped --target 1024
"""

import cv2
import numpy as np
import argparse
import shutil
from pathlib import Path
from PIL import Image

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}


def smart_crop(img_path: Path, target: int) -> Image.Image:
    img_cv = cv2.imread(str(img_path))
    if img_cv is None:
        raise ValueError(f"Could not read: {img_path}")

    h, w = img_cv.shape[:2]

    # Resize shortest side to target
    if w <= h:
        new_w = target
        new_h = int(round(h * target / w))
    else:
        new_h = target
        new_w = int(round(w * target / h))

    resized = cv2.resize(img_cv, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)

    # Saliency — find focal point
    cx, cy = new_w // 2, new_h // 2
    try:
        saliency = cv2.saliency.SpectralResidualSaliency_create()
        ok, sal_map = saliency.computeSaliency(resized)
        if ok:
            sal_u8 = (sal_map * 255).astype(np.uint8)
            thresh_val = int(np.percentile(sal_u8, 60))
            _, thresh = cv2.threshold(sal_u8, thresh_val, 255, cv2.THRESH_BINARY)
            M = cv2.moments(thresh)
            if M["m00"] > 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
    except Exception:
        pass

    # Crop target×target clamped to bounds
    half = target // 2
    x1 = max(0, min(cx - half, new_w - target))
    y1 = max(0, min(cy - half, new_h - target))
    cropped = resized[y1:y1 + target, x1:x1 + target]

    return Image.fromarray(cv2.cvtColor(cropped, cv2.COLOR_BGR2RGB))


def main():
    parser = argparse.ArgumentParser(description="Smart crop images to square")
    parser.add_argument("input_dir",  type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--target",   type=int, default=1024)
    args = parser.parse_args()

    input_dir  = args.input_dir.expanduser().resolve()
    output_dir = args.output_dir.expanduser().resolve()

    images = [p for p in input_dir.rglob("*") if p.suffix.lower() in IMAGE_EXTS]
    print(f"Found {len(images)} images → cropping to {args.target}×{args.target}")

    ok = skipped = errors = 0

    for i, src in enumerate(images):
        # Preserve subfolder structure (subreddit buckets)
        rel     = src.relative_to(input_dir)
        dest    = output_dir / rel.with_suffix(".png")
        dest.parent.mkdir(parents=True, exist_ok=True)

        try:
            img = smart_crop(src, args.target)
            img.save(dest, "PNG")
            ok += 1
        except Exception as e:
            print(f"  ERROR {src.name}: {e}")
            errors += 1

        if (i + 1) % 100 == 0:
            print(f"  {i+1}/{len(images)}")

    print(f"\nDone — {ok} cropped, {errors} errors")
    print(f"Output: {output_dir}")


if __name__ == "__main__":
    main()
