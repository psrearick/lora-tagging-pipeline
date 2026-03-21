# lora-tagging-pipeline

An end-to-end CLI pipeline for building labeled image datasets to train LoRA (Low-Rank Adaptation) fine-tuning models. It downloads images from Reddit (or other sources), filters and deduplicates them, auto-tags them using CLIP against a custom multi-axis taxonomy, and exports training-ready image/caption pairs.

---

## Pipeline Overview

```
Sources (Reddit subreddits, etc.)
    ↓
[download]  →  raw/
    ↓
[filter]    →  accepted/ review/ rejected/   (resolution, sharpness, brightness)
    ↓
[crop]      →  cropped/                      (saliency-aware square crop)
    ↓
[dedupe]    →  cropped/   duplicates/        (perceptual hash deduplication)
    ↓
[clip]      →  clip_labels.json              (CLIP similarity scores per tag)
    ↓
[generate]  →  data.json                     (structured metadata + auto-tags)
    ↓
[review]    →  gallery UI on localhost:8000  (manual tag review + status)
    ↓
[export]    →  training/                     (images + .txt caption sidecars)
```

---

## Prerequisites

- Python 3.12
- [Poetry](https://python-poetry.org/docs/#installation)

```bash
cd app/
poetry install
```

This installs all Python dependencies including `torch`, `open-clip-torch`, `opencv-python`, and `gallery-dl`.

---

## Configuration

Copy the `birds_demo/` folder as a starting point. Three files need to be configured:

### `lora_config.json` — Taxonomy

Defines the tag system, CLIP model settings, and how axes map to LoRA folders.

```json
{
    "project_name": "My LoRA Project",
    "target_size": 1024,
    "clip_threshold": 0.25,
    "clip_model": "ViT-B-32",
    "loras": {
        "lora1_form": ["body_size", "wing_shape"],
        "lora2_head": ["crest", "beak"]
    },
    "axes": {
        "body_size": {
            "tags": {
                "sz_small": {
                    "description": "small bird the size of a sparrow, compact body",
                    "synonyms": ["small bird", "sparrow sized", "compact bird"]
                },
                "sz_large": {
                    "description": "large bird the size of a hawk, big powerful body",
                    "synonyms": ["large bird", "hawk sized", "eagle sized"]
                }
            }
        }
    }
}
```

**Key concepts:**
- **Axes** are independent dimensions (e.g. body size, beak shape, plumage color). An image gets one tag per axis.
- **Tags within an axis are mutually exclusive** — write descriptions as if scoring an image caption.
- **`description`** is what CLIP scores against. Be specific and visual.
- **`synonyms`** are used to generate natural-language captions at export time.
- **`loras`** maps LoRA folder names to the axes they contain. Used with `--group-by-lora` at export.
- **`clip_threshold`** (0–1): minimum CLIP score to auto-assign a tag.

See `birds_demo/lora_config.json` for a full 8-axis example covering body size, wing shape, crest, beak, plumage pattern, color, and tail.

### `env.conf` — Environment

```bash
# List of source names inserted into DOWNLOAD_URL_TEMPLATE (e.g. subreddit names)
SOURCES=("subreddit1" "subreddit2")

# URL pattern for each source. {source} is replaced with each entry in SOURCES,
# {sort} is replaced with SORT below.
DOWNLOAD_URL_TEMPLATE="https://www.reddit.com/r/{source}/{sort}"

# gallery-dl sort/filter appended to each URL. Controls which posts are fetched.
# Examples: "top/?t=all", "top/?t=year", "new"
SORT="top/?t=all"

# Page range to download from each source (gallery-dl --range START-END)
START=1
END=50

# Directory where all pipeline output is written (raw/, cropped/, training/, etc.)
DEST="/path/to/dataset"

# SQLite archive file used by gallery-dl to track already-downloaded files.
# Prevents re-downloading on subsequent runs.
ARCHIVE="/path/to/dataset/dl-archive.sqlite"

# Path to your lora_config.json taxonomy file
LORA_CONFIG="/path/to/your/lora_config.json"

# Path to your gallery_dl.json extractor config file
GALLERY_CONF="/path/to/your/gallery_dl.json"

# Path to the data.json dataset file (created by the generate step, read by review/export)
DATA_FILE="/path/to/dataset/data.json"
```

### `gallery_dl.json` — Downloader

Configures [gallery-dl](https://github.com/mikf/gallery-dl) extractor behavior (Reddit-specific settings, rate limiting, filename patterns). See `birds_demo/gallery_dl.json` for a working example.

---

## Usage

**Run the full pipeline:**
```bash
./app/pipeline.sh --config birds_demo/env.conf all
```

**Run individual steps:**
```bash
./app/pipeline.sh --config <env.conf> download   # fetch images from sources
./app/pipeline.sh --config <env.conf> filter     # quality filter (resolution, sharpness, brightness)
./app/pipeline.sh --config <env.conf> crop       # saliency-aware square crop
./app/pipeline.sh --config <env.conf> dedupe     # remove perceptual duplicates
./app/pipeline.sh --config <env.conf> clip       # score images against taxonomy with CLIP
./app/pipeline.sh --config <env.conf> generate   # build data.json from CLIP scores
./app/pipeline.sh --config <env.conf> review     # start gallery UI at localhost:8000
./app/pipeline.sh --config <env.conf> export     # write training/ folder
```

**Export with LoRA grouping:**
```bash
poetry run python app/export_training.py --data /path/to/data.json --out /path/to/training --group-by-lora
```

---

## Outputs

| File / Folder | Description |
|---|---|
| `accepted/` `review/` `rejected/` | Filter buckets with images sorted by quality |
| `cropped/` | Preprocessed 1024×1024 square crops |
| `duplicates/` | Near-duplicate images moved out of the main set |
| `clip_labels.json` | CLIP similarity scores for every tag on every image |
| `data.json` | Full dataset: images, tags, status, notes, statistics |
| `training/` | Final export: `image.png` + `image.txt` caption pairs |
| `training/<lora_name>/` | Per-LoRA subfolders when grouped by LoRA |

**Caption format** (`.txt` sidecar):
```
small bird, sparrow sized, compact bird, pointed beak, narrow bill, sharp beak
```
Captions are generated by expanding each tag's synonyms — standard format for Stable Diffusion LoRA training tools.

---

## Gallery Review UI

The `review` step starts a local HTTP server and opens `gallery.html` in your browser. From there you can:

- Browse all images with their auto-assigned tags
- Manually add, remove, or override tags
- Set image status: `selected`, `rejected`, `unreviewed`
- Filter by tag, source, or status
- View tag frequency distribution

Only images with `selected` status are included in the export.

---

## Hardware

CLIP scoring (`clip` step) uses the best available device:
- **Apple Silicon**: MPS acceleration
- **NVIDIA**: CUDA
- **Fallback**: CPU (slower but functional)

The `ViT-B-32` CLIP model is the default and works well on consumer hardware. Larger CLIP models can be specified in `lora_config.json` via `"clip_model"`.
