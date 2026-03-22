#!/usr/bin/env python3
"""
CLIP pre-labeler. Reads tag descriptions from lora_config.json.

Usage:
    # Full run
    python3 clip_label.py ~/dataset/sorted/accepted ~/dataset/clip_labels.json

    # Score only new tags, merge into existing
    python3 clip_label.py ~/dataset/sorted/accepted ~/dataset/clip_labels.json \
        --tags tag_one tag_two --update

    # Use a different config file
    python3 clip_label.py ~/dataset/sorted/accepted ~/dataset/clip_labels.json \
        --config ~/dataset/lora_config.json
"""

import json
import torch
import open_clip
import argparse
from PIL import Image
from pathlib import Path
from lora_pipeline.config_loader import load_config

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}


def load_model(model_name: str):
    model, _, preprocess = open_clip.create_model_and_transforms(
        model_name, pretrained="openai", quick_gelu=True
    )
    tokenizer = open_clip.get_tokenizer(model_name)
    model.eval()
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    print(f"Running on: {device}")
    return model.to(device), preprocess, tokenizer, device


def encode_texts(model, tokenizer, device, cfg, tag_descriptions: dict):
    """Encode text prompts with prompt ensembling.

    For each tag, builds a prompt list from its description plus all synonyms,
    wraps each with cfg.prompt_template, encodes all prompts in one batched
    forward pass, then averages and re-normalizes per tag. This is the prompt
    ensembling technique from the original CLIP paper.
    """
    labels: list[str] = list(tag_descriptions.keys())

    # Build per-tag prompt lists
    tag_prompts: list[list[str]] = []
    for tag in labels:
        desc    = tag_descriptions[tag]
        syns    = cfg.synonyms.get(tag, [])
        raw     = [desc] + syns
        prompts = [cfg.prompt_template.format(description=p) for p in raw]
        tag_prompts.append(prompts)

    # Flatten and encode all prompts in a single batched forward pass
    flat_prompts = [p for prompts in tag_prompts for p in prompts]
    tokens = tokenizer(flat_prompts).to(device)
    with torch.no_grad():
        all_features = model.encode_text(tokens)
        all_features /= all_features.norm(dim=-1, keepdim=True)

    # Average embeddings per tag, then re-normalize
    text_features = []
    idx = 0
    for prompts in tag_prompts:
        n   = len(prompts)
        avg = all_features[idx:idx + n].mean(dim=0)
        avg = avg / avg.norm()
        text_features.append(avg)
        idx += n

    return labels, torch.stack(text_features)


def score_image(img_path, model, preprocess, text_features, labels, device):
    try:
        img = preprocess(Image.open(img_path).convert("RGB")).unsqueeze(0).to(device)
        with torch.no_grad():
            img_features = model.encode_image(img)
            img_features /= img_features.norm(dim=-1, keepdim=True)
            scores = (img_features @ text_features.T).squeeze(0)
        return {label: round(float(scores[i]), 4) for i, label in enumerate(labels)}
    except Exception as e:
        print(f"  Error on {img_path.name}: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description="CLIP pre-labeler")
    parser.add_argument("input_dir",  type=Path)
    parser.add_argument("output",     type=Path)
    parser.add_argument("--config",   type=Path, default="lora_config.json")
    parser.add_argument("--tags",     nargs="+", default=None,
                        help="Score only these specific tags. Must exist in config.")
    parser.add_argument("--update",   action="store_true",
                        help="Merge new scores into existing clip_labels.json")
    args = parser.parse_args()

    cfg         = load_config(args.config)
    input_dir   = args.input_dir.expanduser().resolve()
    output_path = args.output.expanduser().resolve()
    base_dir    = output_path.parent

    # Determine which tags to score
    if args.tags:
        missing = [t for t in args.tags if t not in cfg.descriptions]
        if missing:
            print(f"Error: tags not found in config: {missing}")
            raise SystemExit(1)
        tag_descriptions = {t: cfg.descriptions[t] for t in args.tags}
    else:
        tag_descriptions = cfg.descriptions

    print(f"Config   : {args.config}")
    print(f"Project  : {cfg.project_name}")
    print(f"Scoring  : {len(tag_descriptions)} tags")

    # Load existing results if updating
    existing_by_path = {}
    if args.update and output_path.exists():
        with open(output_path) as f:
            for entry in json.load(f):
                existing_by_path[entry["path"]] = entry
        print(f"Merging into {len(existing_by_path)} existing entries")

    print("Loading CLIP model...")
    model, preprocess, tokenizer, device = load_model(cfg.clip_model)
    labels, text_features = encode_texts(model, tokenizer, device, cfg, tag_descriptions)

    images = [p for p in input_dir.rglob("*") if p.suffix.lower() in IMAGE_EXTS]
    print(f"Found {len(images)} images\n")

    results = []
    for i, img_path in enumerate(images):
        try:
            rel_path = str(img_path.relative_to(base_dir))
        except ValueError:
            rel_path = str(img_path)

        new_scores: None|dict[str,float] = score_image(img_path, model, preprocess, text_features, labels, device)
        if new_scores is None:
            continue

        if args.update and rel_path in existing_by_path:
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

    if args.update:
        scored_paths = {r["path"] for r in results}
        for path, entry in existing_by_path.items():
            if path not in scored_paths:
                results.append(entry)

    results.sort(key=lambda x: x["top_score"], reverse=True)

    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nDone — {len(results)} entries → {output_path}")


if __name__ == "__main__":
    main()
