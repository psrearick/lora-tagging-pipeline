import json
from collections import Counter
from pathlib import Path

from lora_pipeline.config import PipelineConfig
from lora_pipeline.config_loader import load_config
from lora_pipeline.pipeline.generate_data import assign_auto_tags


def run(cfg: PipelineConfig, update: bool = True, reclip: bool = True) -> None:
    lora_cfg    = load_config(cfg.lora_config)
    labels_path = cfg.dest / "clip_labels.json"
    out_path    = cfg.data_file
    base_dir    = out_path.parent

    with open(labels_path) as f:
        clip_results = json.load(f)

    clip_by_path = {}
    for entry in clip_results:
        abs_path = Path(entry["path"])
        try:
            rel = str(abs_path.relative_to(base_dir))
        except ValueError:
            rel = str(abs_path)
        clip_by_path[rel] = entry

    if update and out_path.exists():
        print(f"Updating {out_path}...")
        with open(out_path) as f:
            data = json.load(f)

        data["all_tags"]     = lora_cfg.all_tags
        data["axis_groups"]  = lora_cfg.axis_groups
        data["tag_synonyms"] = lora_cfg.synonyms

        existing_sources = set(data.get("sources", []))
        for entry in clip_results:
            existing_sources.add(entry.get("source", "unknown"))
        data["sources"] = sorted(existing_sources)

        existing_paths = {img["path"] for img in data["images"]}
        updated = added = skipped = 0

        all_tags_set = set(lora_cfg.all_tags)
        for img in data["images"]:
            clip = clip_by_path.get(img["path"])
            if clip is None:
                skipped += 1
                continue
            img["clip_scores"] = clip.get("scores", img.get("clip_scores", {}))
            if reclip or "tags" not in img:
                if img.get("status", "unreviewed") == "unreviewed":
                    img["tags"] = assign_auto_tags(img["clip_scores"], lora_cfg)
                else:
                    img["tags"] = [t for t in img.get("tags", []) if t in all_tags_set]
                updated += 1
            if "excluded_from" not in img:
                img["excluded_from"] = []

        max_id = max((img["id"] for img in data["images"]), default=-1)
        for rel_path, entry in clip_by_path.items():
            if rel_path in existing_paths:
                continue
            max_id += 1
            data["images"].append({
                "id":          max_id,
                "path":        rel_path,
                "source":      entry.get("source", "unknown"),
                "clip_scores": entry.get("scores", {}),
                "tags":        assign_auto_tags(entry.get("scores", {}), lora_cfg),
                "manual_tags": [],
                "status":      "unreviewed",
                "notes":       "",
                "excluded_from": []
            })
            added += 1

        print(f"  Updated: {updated}  Added: {added}  Skipped: {skipped}")

    else:
        images  = []
        sources = set()
        for i, entry in enumerate(clip_results):
            abs_path = Path(entry["path"])
            try:
                rel_path = str(abs_path.relative_to(base_dir))
            except ValueError:
                rel_path = str(abs_path)
            source = entry.get("source", "unknown")
            sources.add(source)
            images.append({
                "id":          i,
                "path":        rel_path,
                "source":      source,
                "clip_scores": entry.get("scores", {}),
                "tags":        assign_auto_tags(entry.get("scores", {}), lora_cfg),
                "manual_tags": [],
                "status":      "unreviewed",
                "notes":       "",
            })
        data = {
            "version":      1,
            "all_tags":     lora_cfg.all_tags,
            "axis_groups":  lora_cfg.axis_groups,
            "tag_synonyms": lora_cfg.synonyms,
            "sources":      sorted(sources),
            "lastModified": 0,
            "images":       images,
        }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(data, f, indent=2)

    print(f"\nWrote {out_path}  ({len(data['images'])} images)")

    tag_counts = Counter(tag for img in data["images"] for tag in img["tags"])
    for axis, axis_tags in lora_cfg.axis_groups.items():
        print(f"\n  [{axis}]")
        for tag in axis_tags:
            n   = tag_counts.get(tag, 0)
            bar = "█" * (n // 5)
            print(f"    {lora_cfg.display_name(tag):30} ({tag})  {n:4}  {bar}")
