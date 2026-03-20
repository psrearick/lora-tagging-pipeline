#!/usr/bin/env python3
"""
LoRA training dataset quality filter.
Run after gallery-dl. Sorts raw downloads into accepted / review / rejected.

Requirements: pip3 install opencv-python-headless

Usage:
    python3 filter_dataset.py ~/dataset/raw ~/dataset/sorted
    python3 filter_dataset.py ~/dataset/raw ~/dataset/sorted --sharpness-accept 100 --min-width 1024
"""

import cv2
import json
import shutil
import logging
import argparse
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


@dataclass
class FilterConfig:
    min_width: int = 768
    min_height: int = 768
    sharpness_accept: float = 80.0
    sharpness_review: float = 40.0
    min_brightness: float = 35.0
    max_brightness: float = 215.0


@dataclass
class ImageResult:
    path: str
    bucket: str
    verdict: str
    reason: str
    width: int = 0
    height: int = 0
    sharpness: float = 0.0
    brightness: float = 0.0


def load_image(path: Path) -> Optional[cv2.Mat]:
    img = cv2.imread(str(path))
    if img is None:
        logging.warning(f"Could not read: {path.name}")
    return img


def measure_sharpness(img) -> float:
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def measure_brightness(img) -> float:
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return float(gray.mean())


def estimate_zoom(img) -> str:
    h, w = img.shape[:2]
    ratio = w / h
    if ratio < 0.65:
        return "likely_full_body"
    elif ratio < 1.1:
        return "likely_mid"
    else:
        return "likely_close"


def classify(img, path: Path, bucket: str, cfg: FilterConfig) -> ImageResult:
    h, w = img.shape[:2]
    base = ImageResult(path=str(path), bucket=bucket, verdict="", reason="")
    base.width = w
    base.height = h

    if w < cfg.min_width or h < cfg.min_height:
        base.verdict = "rejected"
        base.reason = f"resolution_{w}x{h}"
        return base

    sharpness = measure_sharpness(img)
    brightness = measure_brightness(img)
    base.sharpness = round(sharpness, 2)
    base.brightness = round(brightness, 2)

    if brightness < cfg.min_brightness:
        base.verdict = "rejected"
        base.reason = f"too_dark_{round(brightness, 1)}"
        return base

    if brightness > cfg.max_brightness:
        base.verdict = "rejected"
        base.reason = f"blown_out_{round(brightness, 1)}"
        return base

    if sharpness >= cfg.sharpness_accept:
        base.verdict = "accepted"
        base.reason = f"sharp_{round(sharpness, 1)}"
    elif sharpness >= cfg.sharpness_review:
        base.verdict = "review"
        base.reason = f"borderline_{round(sharpness, 1)}"
    else:
        base.verdict = "rejected"
        base.reason = f"blurry_{round(sharpness, 1)}"

    base.reason += f"_zoom_{estimate_zoom(img)}"
    return base


def process_directory(raw_dir: Path, out_dir: Path, cfg: FilterConfig) -> dict:
    image_exts = {".jpg", ".jpeg", ".png", ".webp"}
    stats = {"accepted": 0, "review": 0, "rejected": 0, "errors": 0, "total": 0}
    log_path = out_dir / "filter_log.jsonl"
    out_dir.mkdir(parents=True, exist_ok=True)

    for bucket_dir in sorted(raw_dir.iterdir()):
        if not bucket_dir.is_dir():
            continue

        bucket = bucket_dir.name
        logging.info(f"Processing bucket: {bucket}")

        for img_path in sorted(bucket_dir.rglob("*")):
            if img_path.suffix.lower() not in image_exts:
                continue

            stats["total"] += 1

            try:
                img = load_image(img_path)
                if img is None:
                    stats["errors"] += 1
                    continue

                result = classify(img, img_path, bucket, cfg)

                dest_dir = out_dir / result.verdict / bucket
                dest_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(img_path, dest_dir / img_path.name)

                stats[result.verdict] += 1

                with open(log_path, "a") as f:
                    json.dump(asdict(result), f)
                    f.write("\n")

            except Exception as e:
                logging.error(f"Failed on {img_path.name}: {e}")
                stats["errors"] += 1

    return stats


def main():
    parser = argparse.ArgumentParser(description="LoRA dataset quality filter")
    parser.add_argument("input_dir", type=Path, help="gallery-dl raw output directory")
    parser.add_argument("output_dir", type=Path, help="Sorted output directory")
    parser.add_argument("--min-width", type=int, default=768)
    parser.add_argument("--min-height", type=int, default=768)
    parser.add_argument("--sharpness-accept", type=float, default=80.0)
    parser.add_argument("--sharpness-review", type=float, default=40.0)
    parser.add_argument("--min-brightness", type=float, default=35.0)
    parser.add_argument("--max-brightness", type=float, default=215.0)
    args = parser.parse_args()

    cfg = FilterConfig(
        min_width=args.min_width,
        min_height=args.min_height,
        sharpness_accept=args.sharpness_accept,
        sharpness_review=args.sharpness_review,
        min_brightness=args.min_brightness,
        max_brightness=args.max_brightness,
    )

    logging.info(f"Input:  {args.input_dir}")
    logging.info(f"Output: {args.output_dir}")
    logging.info(f"Config: {cfg}")

    stats = process_directory(args.input_dir, args.output_dir, cfg)

    print("\n--- Results ---")
    for key, val in stats.items():
        print(f"  {key:12}: {val}")

    if stats["total"] > 0:
        accept_rate = stats["accepted"] / stats["total"] * 100
        print(f"\n  Accept rate: {accept_rate:.1f}%")


if __name__ == "__main__":
    main()
