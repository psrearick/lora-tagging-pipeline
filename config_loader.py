"""
Shared config loader. Every script imports this.
Usage:
    from config_loader import load_config
    cfg = load_config("lora_config.json")

    cfg.all_tags          → ["phstyle_bare", ...]
    cfg.axis_groups       → {"style": ["phstyle_bare", ...], ...}
    cfg.descriptions      → {"phstyle_bare": "completely smooth...", ...}
    cfg.synonyms          → {"phstyle_bare": ["bare", "shaved", ...], ...}
    cfg.display_name(tag) → "bare"   (first synonym)
    cfg.tag_to_lora       → {"phstyle_bare": "lora1_style_density", ...}
    cfg.loras             → {"lora1_style_density": ["style", "density"], ...}
    cfg.threshold         → 0.40
    cfg.clip_model        → "ViT-B-32"
    cfg.target_size       → 1024
"""

import json
from pathlib import Path


class Config:
    def __init__(self, raw: dict):
        self._raw = raw

        self.project_name = raw.get("project_name", "lora_project")
        self.target_size  = raw.get("target_size", 1024)
        self.threshold    = raw.get("clip_threshold", 0.40)
        self.clip_model   = raw.get("clip_model", "ViT-B-32")
        self.loras        = raw.get("loras", {})

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
