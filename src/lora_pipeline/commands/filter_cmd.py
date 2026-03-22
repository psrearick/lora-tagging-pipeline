from pathlib import Path

from lora_pipeline.config import PipelineConfig
from lora_pipeline.pipeline.filter_dataset import FilterConfig, process_directory


def run(
    cfg: PipelineConfig,
    min_width: int = 1024,
    min_height: int = 1024,
    sharpness_accept: float = 80.0,
    sharpness_review: float = 40.0,
    min_brightness: float = 35.0,
    max_brightness: float = 215.0,
) -> None:
    print("=== Filtering dataset ===")
    filter_cfg = FilterConfig(
        min_width=min_width,
        min_height=min_height,
        sharpness_accept=sharpness_accept,
        sharpness_review=sharpness_review,
        min_brightness=min_brightness,
        max_brightness=max_brightness,
    )
    stats = process_directory(cfg.dest / "raw", cfg.dest / "filtered", filter_cfg)
    print("\n--- Results ---")
    for key, val in stats.items():
        print(f"  {key:12}: {val}")
    if stats["total"] > 0:
        accept_rate = stats["accepted"] / stats["total"] * 100
        print(f"\n  Accept rate: {accept_rate:.1f}%")
    print("=== Done ===")
