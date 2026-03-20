#!/usr/bin/env python3
"""
CLIP pre-labeler for LoRA dataset buckets.

Usage:
    # Full run — score all tags, write fresh clip_labels.json
    python3 clip_label.py ~/dataset/sorted/accepted ~/dataset/clip_labels.json

    # Partial run — score only new tags, merge into existing clip_labels.json
    python3 clip_label.py ~/dataset/sorted/accepted ~/dataset/clip_labels.json \
        --tags pos_standing pos_sitting pos_kneeling pos_lying_back pos_lying_side \
               pos_all_fours pos_squatting int_natural int_spreading int_touching int_toy \
        --update
"""

import json
import torch
import open_clip
import argparse
from PIL import Image
from pathlib import Path
import sys

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}

# Every tag mapped to its natural language description.
# Add new tags here when you add new axis groups.
BUCKETS = {
    # LoRA 1 — Style + Density
    "phstyle_bare":       "completely smooth shaved vulva with no pubic hair whatsoever",
    "phstyle_stubble":    "very short stubble regrowth after shaving pubic area",
    "phstyle_strip":      "narrow vertical landing strip of pubic hair centered above vulva",
    "phstyle_trimmed":    "neatly trimmed short pubic hair keeping natural shape",
    "phstyle_bush":       "full untrimmed natural ungroomed pubic hair",
    "phdns_sparse":       "sparse thin low-density pubic hair with visible skin beneath",
    "phdns_moderate":     "medium density pubic hair neither sparse nor thick",
    "phdns_thick":        "thick dense full high-density pubic hair",
    # LoRA 2 — Length
    "phlen_stubble":      "pubic hair under three millimeters very close cropped",
    "phlen_short":        "pubic hair three to eight millimeters short trimmed",
    "phlen_medium":       "pubic hair eight to twenty millimeters medium length",
    "phlen_long":         "pubic hair over twenty millimeters long natural growth",
    # LoRA 3 — Texture
    "phtex_straight":     "straight smooth pubic hair with no curl",
    "phtex_wavy":         "gently wavy pubic hair slight curl pattern",
    "phtex_curly":        "clearly curly pubic hair tight curl pattern",
    "phtex_coily":        "tightly coiled kinky pubic hair very tight curl",
    # LoRA 4 — Anatomy
    "lmaj_flat":          "female genitalia with flat minimal outer labia majora close together low profile",
    "lmaj_full":          "female genitalia with full prominent large outer labia majora high volume",
    "lmin_tucked":        "female genitalia with inner labia minora completely tucked inside outer labia not visible",
    "lmin_protruding":    "female genitalia with inner labia minora protruding extending visibly beyond outer labia",
    "hood_covered":       "female genitalia with clitoral hood fully covering clitoris glans not visible at rest",
    "hood_exposed":       "female genitalia with clitoral hood retracted minimal coverage clitoris glans visible",
    # LoRA 5 — Position
    "pos_standing":       "person standing upright fully vertical on both feet",
    "pos_sitting":        "person sitting on surface with torso upright",
    "pos_kneeling":       "person kneeling on one or both knees",
    "pos_lying_back":     "person lying flat on their back face up supine",
    "pos_lying_side":     "person lying on their side",
    "pos_all_fours":      "person on hands and knees on all fours",
    "pos_squatting":      "person squatting low with knees bent wide apart",
    # LoRA 5 — Interaction
    "int_natural":        "no hands touching genitals hands away from body",
    "int_spreading":      "fingers spreading labia apart pulling open with hands",
    "int_touching":       "hand touching or rubbing genitals without spreading open",
    "int_toy":            "sex toy vibrator dildo in use inserted or held against genitals",
}


def load_model():
    model, _, preprocess = open_clip.create_model_and_transforms(
        "ViT-B-32", pretrained="openai", precision="fp32", quick_gelu=True
    )
    tokenizer = open_clip.get_tokenizer("ViT-B-32")
    model.eval()
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    print(f"Running on: {device}")
    return model.to(device), preprocess, tokenizer, device


def encode_texts(model, tokenizer, device, tag_subset):
    labels       = list(tag_subset.keys())
    descriptions = list(tag_subset.values())
    tokens = tokenizer(descriptions).to(device)
    with torch.no_grad():
        text_features = model.encode_text(tokens)
        text_features /= text_features.norm(dim=-1, keepdim=True)
    return labels, text_features


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
    parser.add_argument("input_dir",    type=Path, help="Directory of accepted images")
    parser.add_argument("output",       type=Path, help="clip_labels.json to write or update")
    parser.add_argument("--tags",       nargs="+",  default=None,
                        help="Score only these specific tags (must exist in BUCKETS). "
                             "If omitted, scores all tags.")
    parser.add_argument("--update",     action="store_true",
                        help="Merge new scores into existing clip_labels.json "
                             "instead of overwriting. Required when using --tags on new axes.")
    args = parser.parse_args()

    input_dir   = args.input_dir.expanduser().resolve()
    output_path = args.output.expanduser().resolve()
    base_dir    = output_path.parent

    # Determine which tags to score this run
    if args.tags:
        missing = [t for t in args.tags if t not in BUCKETS]
        if missing:
            print(f"Error: these tags are not in BUCKETS: {missing}")
            print("Add them with descriptions before scoring.")
            sys.exit(1)
        tag_subset = {t: BUCKETS[t] for t in args.tags}
        print(f"Scoring {len(tag_subset)} tags: {list(tag_subset.keys())}")
    else:
        tag_subset = BUCKETS
        print(f"Scoring all {len(tag_subset)} tags")

    # Load existing results if updating
    existing_by_path = {}
    if args.update and output_path.exists():
        with open(output_path) as f:
            existing = json.load(f)
        for entry in existing:
            existing_by_path[entry["path"]] = entry
        print(f"Loaded {len(existing_by_path)} existing entries to merge into")

    print("Loading CLIP model...")
    model, preprocess, tokenizer, device = load_model()
    labels, text_features = encode_texts(model, tokenizer, device, tag_subset)

    images = [p for p in input_dir.rglob("*") if p.suffix.lower() in IMAGE_EXTS]
    total  = len(images)
    print(f"Found {total} images")

    results = []
    for i, img_path in enumerate(images):
        try:
            rel_path = str(img_path.relative_to(base_dir))
        except ValueError:
            rel_path = str(img_path)

        new_scores = score_image(img_path, model, preprocess, text_features, labels, device)
        if new_scores is None:
            continue

        if args.update and rel_path in existing_by_path:
            # Merge — add new tag scores into existing scores dict, keep old ones intact
            entry = existing_by_path[rel_path]
            entry["scores"].update(new_scores)
            # Refresh top_bucket across ALL scores now that we have more
            entry["top_bucket"] = max(entry["scores"], key=entry["scores"].get)
            entry["top_score"]  = entry["scores"][entry["top_bucket"]]
            results.append(entry)
        else:
            # New image or fresh run
            top_bucket = max(new_scores, key=new_scores.get)
            results.append({
                "path":       rel_path,
                "subreddit":  img_path.parent.name,
                "top_bucket": top_bucket,
                "top_score":  new_scores[top_bucket],
                "scores":     new_scores,
            })

        if i % 50 == 0:
            print(f"  {i}/{total}")

    # If updating, include any existing entries for images not on disk anymore
    # (they may have been moved to duplicates/rejected folders — keep their scores)
    if args.update:
        scored_paths = {r["path"] for r in results}
        for path, entry in existing_by_path.items():
            if path not in scored_paths:
                results.append(entry)

    results.sort(key=lambda x: x["top_score"], reverse=True)

    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nDone — {len(results)} entries written to {output_path}")


if __name__ == "__main__":
    main()
