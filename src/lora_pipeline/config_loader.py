"""
Shared config loader. Every script imports this.
Usage:
    from lora_pipeline.config_loader import load_config
    cfg = load_config("lora_config.json")

    cfg.all_tags          → ["axis1_tag1", ...]
    cfg.axis_groups       → {"axis1": ["axis1_tag1", ...], ...}
    cfg.descriptions      → {"axis1_tag1": "description text...", ...}
    cfg.synonyms          → {"axis1_tag1": ["label", "synonym", ...], ...}
    cfg.display_name(tag) → "label"  (first synonym)
    cfg.tag_to_lora       → {"axis1_tag1": "lora1_name", ...}
    cfg.loras             → {"lora1_name": ["axis1", "axis2"], ...}
    cfg.threshold         → 0.40
    cfg.clip_model        → "ViT-B-32"
    cfg.target_size       → 1024
"""

import json
from pathlib import Path


class Config:
    def __init__(self, raw: dict):
        self._raw = raw

        self.project_name    = raw.get("project_name", "lora_project")
        self.target_size     = raw.get("target_size", 1024)
        self.threshold       = raw.get("clip_threshold", 0.40)
        self.clip_model      = raw.get("clip_model", "ViT-B-32")
        self.prompt_template = raw.get("prompt_template", "{description}")
        self.loras           = raw.get("loras", {})

        # Derived structures built once at load time
        self.axis_groups  = {}   # axis_name → [tag, ...]
        self.descriptions = {}   # tag → clip description string
        self.synonyms     = {}   # tag → [synonym, ...]
        self.tag_to_lora  = {}   # tag → lora folder name

        for axis_name, axis_data in raw.get("axes", {}).items():
            tags_in_axis = []
            for tag, tag_data in axis_data.get("tags", {}).items():
                tags_in_axis.append(tag)
                self.descriptions[tag] = tag_data.get("description", tag)
                self.synonyms[tag]     = tag_data.get("synonyms", [tag])
            self.axis_groups[axis_name] = tags_in_axis

        # Build tag → lora reverse map
        for lora_name, axes in self.loras.items():
            for axis in axes:
                for tag in self.axis_groups.get(axis, []):
                    self.tag_to_lora[tag] = lora_name

        self.all_tags = [t for tags in self.axis_groups.values() for t in tags]

    def display_name(self, tag: str) -> str:
        """First synonym for a tag — what the UI shows instead of the raw token."""
        syns = self.synonyms.get(tag, [])
        return syns[0] if syns else tag

    def all_loras_for_tags(self, tags: list) -> list:
        """Return every LoRA folder name this set of tags belongs to."""
        matched = set()
        for tag in tags:
            if tag in self.tag_to_lora:
                matched.add(self.tag_to_lora[tag])
        return sorted(matched) if matched else ["unassigned"]

    def make_caption(self, tags: list) -> str:
        """Expand tags to synonym lists for caption sidecar files."""
        terms = []
        for tag in tags:
            terms.extend(self.synonyms.get(tag, [tag]))
        return ", ".join(terms)


def load_config(path: str | Path = "lora_config.json") -> Config:
    p = Path(path).expanduser().resolve()
    if not p.exists():
        raise FileNotFoundError(f"Config not found: {p}")
    with open(p) as f:
        return Config(json.load(f))
