#!/usr/bin/env python3
"""
CLIP pre-labeler for LoRA dataset buckets.
Scores each image against natural-language bucket descriptions.
Outputs a ranked candidates JSON you review rather than label from scratch.

Usage: python3 clip_label.py ~/dataset/sorted/accepted ~/dataset/clip_labels.json
"""

import json
import torch
import open_clip
from PIL import Image
from pathlib import Path
import sys

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}

# Describe each bucket in plain language — more specific = better signal
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
}

def load_model():
    model, _, preprocess = open_clip.create_model_and_transforms(
        "ViT-B-32", pretrained="openai"
    )
    tokenizer = open_clip.get_tokenizer("ViT-B-32")
    model.eval()
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    return model.to(device), preprocess, tokenizer, device

def encode_texts(model, tokenizer, device):
    labels = list(BUCKETS.keys())
    descriptions = list(BUCKETS.values())
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
        return None

def main():
    accepted_dir = Path(sys.argv[1])
    output_path = Path(sys.argv[2])

    print("Loading CLIP model...")
    model, preprocess, tokenizer, device = load_model()
    print(f"Running on: {device}")
    labels, text_features = encode_texts(model, tokenizer, device)

    results = []
    images = [p for p in accepted_dir.rglob("*") if p.suffix.lower() in IMAGE_EXTS]
    total = len(images)

    for i, img_path in enumerate(images):
        scores = score_image(img_path, model, preprocess, text_features, labels, device)
        if scores is None:
            continue

        top_bucket = max(scores, key=scores.get)
        top_score = scores[top_bucket]
        results.append({
            "path": str(img_path),
            "top_bucket": top_bucket,
            "top_score": top_score,
            "scores": scores,
            "subreddit": img_path.parent.name
        })

        if i % 50 == 0:
            print(f"  {i}/{total} — {img_path.name} → {top_bucket} ({top_score:.3f})")

    # Sort by confidence descending — highest certainty images first
    results.sort(key=lambda x: x["top_score"], reverse=True)

    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nDone. {len(results)} images labeled → {output_path}")

    # Quick summary
    from collections import Counter
    counts = Counter(r["top_bucket"] for r in results)
    print("\nBucket distribution:")
    for bucket, count in sorted(counts.items()):
        print(f"  {bucket:25}: {count}")

if __name__ == "__main__":
    main()
