import json
from pathlib import Path
from PIL import Image

from lora_pipeline.config import PipelineConfig
from lora_pipeline.config_loader import load_config


def run(cfg: PipelineConfig, group_by_lora: bool = True, status: list[str] | None = None) -> None:
    if status is None:
        status = ["selected"]

    lora_cfg  = load_config(cfg.lora_config)
    base_dir  = cfg.dest
    out_dir   = base_dir / "training"
    data_path = cfg.data_file

    with open(data_path) as f:
        data = json.load(f)

    exportable = [img for img in data.get("images", []) if img.get("status") in status]

    print(f"Project        : {lora_cfg.project_name}")
    print(f"Exporting      : {len(exportable)} images")
    print(f"Group by LoRA  : {'yes' if group_by_lora else 'no'}")
    print()

    out_dir.mkdir(parents=True, exist_ok=True)
    exported = skipped = errors = 0
    lora_counts: dict[str, int] = {}

    for img in exportable:
        src = base_dir / img["path"]
        if not src.exists():
            print(f"  SKIP (missing): {img['path']}")
            skipped += 1
            continue

        tags    = img.get("tags", []) + img.get("manual_tags", [])
        caption = lora_cfg.make_caption(tags)
        stem    = src.stem

        dest_dirs = (
            [out_dir / lora for lora in lora_cfg.all_loras_for_tags(tags)]
            if group_by_lora
            else [out_dir]
        )

        try:
            pil_img = Image.open(src).convert("RGB")
            for dest_dir in dest_dirs:
                dest_dir.mkdir(parents=True, exist_ok=True)
                pil_img.save(dest_dir / f"{stem}.png", "PNG")
                (dest_dir / f"{stem}.txt").write_text(caption, encoding="utf-8")
                lora_counts[dest_dir.name] = lora_counts.get(dest_dir.name, 0) + 1
            exported += 1
            if exported % 50 == 0:
                print(f"  {exported}/{len(exportable)}...")
        except Exception as e:
            print(f"  ERROR {src.name}: {e}")
            errors += 1

    print(f"\nExported : {exported}")
    print(f"Skipped  : {skipped}")
    print(f"Errors   : {errors}")
    if lora_counts:
        print("\nBy folder:")
        for folder, count in sorted(lora_counts.items()):
            print(f"  {folder:35} {count}")
