import json
import torch
import open_clip
from pathlib import Path
from PIL import Image

from lora_pipeline.config import PipelineConfig
from lora_pipeline.config_loader import load_config
from lora_pipeline.pipeline.clip_label import load_model, encode_texts, score_image

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}


def run(cfg: PipelineConfig, tags: list[str] | None = None, update: bool = False) -> None:
    lora_cfg    = load_config(cfg.lora_config)
    input_dir   = cfg.dest / "cropped"
    output_path = cfg.dest / "clip_labels.json"
    base_dir    = cfg.dest

    if tags:
        missing = [t for t in tags if t not in lora_cfg.descriptions]
        if missing:
            raise ValueError(f"Tags not found in config: {missing}")
        tag_descriptions = {t: lora_cfg.descriptions[t] for t in tags}
    else:
        tag_descriptions = lora_cfg.descriptions

    print(f"Config   : {cfg.lora_config}")
    print(f"Project  : {lora_cfg.project_name}")
    print(f"Scoring  : {len(tag_descriptions)} tags")

    existing_by_path = {}
    if update and output_path.exists():
        with open(output_path) as f:
            for entry in json.load(f):
                existing_by_path[entry["path"]] = entry
        print(f"Merging into {len(existing_by_path)} existing entries")

    print("Loading CLIP model...")
    model, preprocess, tokenizer, device = load_model(lora_cfg.clip_model)
    labels, text_features = encode_texts(model, tokenizer, device, tag_descriptions)

    images = [p for p in input_dir.rglob("*") if p.suffix.lower() in IMAGE_EXTS]
    print(f"Found {len(images)} images\n")

    results = []
    for i, img_path in enumerate(images):
        try:
            rel_path = str(img_path.relative_to(base_dir))
        except ValueError:
            rel_path = str(img_path)

        new_scores = score_image(img_path, model, preprocess, text_features, labels, device)
        if new_scores is None:
            continue

        if update and rel_path in existing_by_path:
            entry = existing_by_path[rel_path]
            entry["scores"].update(new_scores)
            entry["top_bucket"] = max(entry["scores"], key=entry["scores"].get)
            entry["top_score"]  = entry["scores"][entry["top_bucket"]]
            results.append(entry)
        else:
            top_bucket = max(new_scores, key=lambda k: new_scores.get(k) or 0 if new_scores else 0)
            results.append({
                "path":       rel_path,
                "source":     img_path.parent.name,
                "top_bucket": top_bucket,
                "top_score":  new_scores[top_bucket],
                "scores":     new_scores,
            })

        if (i + 1) % 50 == 0:
            print(f"  {i+1}/{len(images)}")

    if update:
        scored_paths = {r["path"] for r in results}
        for path, entry in existing_by_path.items():
            if path not in scored_paths:
                results.append(entry)

    results.sort(key=lambda x: x["top_score"], reverse=True)

    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nDone — {len(results)} entries → {output_path}")
