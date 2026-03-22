"""
Parse env.conf (bash-style key=value / key=(...) syntax) into a typed dataclass.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class PipelineConfig:
    sources: list[str]
    download_url_template: str
    sort: str
    start: int
    end: int
    dest: Path
    archive: Path
    lora_config: Path
    gallery_conf: Path
    data_file: Path


def _strip_quotes(value: str) -> str:
    value = value.strip()
    if (value.startswith('"') and value.endswith('"')) or \
       (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    return value


def _parse_env_conf(path: Path) -> dict[str, str | list[str]]:
    """Parse a bash env.conf into a dict of str or list[str] values."""
    text = path.read_text()
    result: dict[str, str | list[str]] = {}

    # Strip comments
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#") or not stripped:
            continue
        # Inline comment: only strip if # is after whitespace (not inside quotes)
        lines.append(stripped)

    i = 0
    while i < len(lines):
        line = lines[i]

        # Array assignment: KEY=(
        array_match = re.match(r'^(\w+)=\((.*)$', line)
        if array_match:
            key = array_match.group(1)
            rest = array_match.group(2).strip()
            items: list[str] = []
            # Values on same line as opening paren
            if rest and rest != ")":
                for item in rest.split():
                    items.append(_strip_quotes(item))
            # Consume continuation lines until closing paren
            i += 1
            while i < len(lines):
                l = lines[i].strip()
                if l == ")":
                    i += 1
                    break
                if l.endswith(")"):
                    l = l[:-1].strip()
                    if l:
                        items.append(_strip_quotes(l))
                    i += 1
                    break
                if l:
                    items.append(_strip_quotes(l))
                i += 1
            result[key] = items
            continue

        # Simple assignment: KEY=value
        simple_match = re.match(r'^(\w+)=(.*)$', line)
        if simple_match:
            key = simple_match.group(1)
            value = simple_match.group(2)
            # Strip inline comment (only if not inside quotes)
            if not (value.startswith('"') or value.startswith("'")):
                value = value.split("#")[0].strip()
            result[key] = _strip_quotes(value)
        i += 1

    return result


def load_pipeline_config(config_path: str) -> PipelineConfig:
    path = Path(config_path).expanduser().resolve()
    raw = _parse_env_conf(path)
    base = path.parent

    def as_path(key: str) -> Path:
        val = raw[key]
        assert isinstance(val, str)
        p = Path(val).expanduser()
        return p if p.is_absolute() else (base / p).resolve()

    def as_str(key: str) -> str:
        val = raw[key]
        assert isinstance(val, str)
        return val

    def as_int(key: str) -> int:
        return int(as_str(key))

    def as_list(key: str) -> list[str]:
        val = raw[key]
        assert isinstance(val, list)
        return val

    return PipelineConfig(
        sources=as_list("SOURCES"),
        download_url_template=as_str("DOWNLOAD_URL_TEMPLATE"),
        sort=as_str("SORT"),
        start=as_int("START"),
        end=as_int("END"),
        dest=as_path("DEST"),
        archive=as_path("ARCHIVE"),
        lora_config=as_path("LORA_CONFIG"),
        gallery_conf=as_path("GALLERY_CONF"),
        data_file=as_path("DATA_FILE"),
    )
