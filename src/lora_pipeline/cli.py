"""
lora-pipeline — unified CLI entry point.

Usage:
    lora-pipeline --config path/to/env.conf <command>

Commands:
    download        Download images from configured sources
    filter          Filter raw images by quality metrics
    crop            Smart-crop filtered images to square
    dedupe          Remove near-duplicate images
    clip            Score images with CLIP embeddings
    generate        Build data.json from CLIP scores
    review          Start review server and open gallery
    export          Export training dataset
    start           Start the HTTP review server
    stop            Stop the HTTP review server
    update-gallery  Copy gallery.html to dataset directory
    sort-log        Print sharpness-ranked images from filter log
    all             Run the complete pipeline (download→generate→review)
"""

import shutil
import click
from importlib.resources import files

from lora_pipeline.config import load_pipeline_config, PipelineConfig


@click.group()
@click.option(
    "--config", "config_path",
    required=True,
    type=click.Path(exists=True),
    help="Path to env.conf",
)
@click.pass_context
def cli(ctx: click.Context, config_path: str) -> None:
    ctx.ensure_object(dict)
    ctx.obj["config"] = load_pipeline_config(config_path)


@cli.command()
@click.pass_obj
def download(obj: dict) -> None:
    """Download images from configured sources."""
    from lora_pipeline.commands import download as dl
    dl.run(obj["config"])


@cli.command()
@click.option("--min-width",        type=int,   default=1024, show_default=True)
@click.option("--min-height",       type=int,   default=1024, show_default=True)
@click.option("--sharpness-accept", type=float, default=80.0, show_default=True)
@click.option("--sharpness-review", type=float, default=40.0, show_default=True)
@click.option("--min-brightness",   type=float, default=35.0, show_default=True)
@click.option("--max-brightness",   type=float, default=215.0, show_default=True)
@click.pass_obj
def filter(
    obj: dict,
    min_width: int,
    min_height: int,
    sharpness_accept: float,
    sharpness_review: float,
    min_brightness: float,
    max_brightness: float,
) -> None:
    """Filter raw images by quality metrics."""
    from lora_pipeline.commands import filter_cmd
    filter_cmd.run(
        obj["config"],
        min_width=min_width,
        min_height=min_height,
        sharpness_accept=sharpness_accept,
        sharpness_review=sharpness_review,
        min_brightness=min_brightness,
        max_brightness=max_brightness,
    )


@cli.command()
@click.pass_obj
def crop(obj: dict) -> None:
    """Smart-crop filtered images to square."""
    from lora_pipeline.commands import crop_cmd
    crop_cmd.run(obj["config"])


@cli.command()
@click.pass_obj
def dedupe(obj: dict) -> None:
    """Remove near-duplicate images."""
    from lora_pipeline.commands import dedupe_cmd
    dedupe_cmd.run(obj["config"])


@cli.command()
@click.option("--tags",   multiple=True, default=None, help="Score only these tags.")
@click.option("--update", is_flag=True,  default=False, help="Merge into existing clip_labels.json.")
@click.pass_obj
def clip(obj: dict, tags: tuple, update: bool) -> None:
    """Score images with CLIP embeddings."""
    from lora_pipeline.commands import clip_cmd
    clip_cmd.run(obj["config"], tags=list(tags) if tags else None, update=update)


@cli.command()
@click.option("--update", is_flag=True, default=True,  help="Merge into existing data.json.")
@click.option("--reclip", is_flag=True, default=True,  help="Re-assign auto-tags from CLIP scores.")
@click.pass_obj
def generate(obj: dict, update: bool, reclip: bool) -> None:
    """Build data.json from CLIP scores."""
    from lora_pipeline.commands import generate_cmd
    generate_cmd.run(obj["config"], update=update, reclip=reclip)


@cli.command()
@click.pass_obj
def review(obj: dict) -> None:
    """Start review server and open gallery."""
    from lora_pipeline.commands import review_cmd
    review_cmd.run(obj["config"])


@cli.command()
@click.option("--group-by-lora", is_flag=True, default=True,  help="Organize output by LoRA folder.")
@click.option("--status",        multiple=True, default=["selected"], help="Export images with these statuses.")
@click.pass_obj
def export(obj: dict, group_by_lora: bool, status: tuple) -> None:
    """Export training dataset."""
    from lora_pipeline.commands import export_cmd
    export_cmd.run(obj["config"], group_by_lora=group_by_lora, status=list(status))


@cli.command()
@click.pass_obj
def start(obj: dict) -> None:
    """Start the HTTP review server."""
    from lora_pipeline.commands import server
    server.start(obj["config"].dest)


@cli.command()
@click.pass_obj
def stop(obj: dict) -> None:
    """Stop the HTTP review server."""
    from lora_pipeline.commands import server
    server.stop()


@cli.command("update-gallery")
@click.pass_obj
def update_gallery(obj: dict) -> None:
    """Copy gallery.html to dataset directory."""
    cfg: PipelineConfig = obj["config"]
    gallery_src = files("lora_pipeline.data").joinpath("gallery.html")
    dest = cfg.dest / "gallery.html"
    shutil.copy2(str(gallery_src), dest)
    print(f"Copied gallery.html → {dest}")


@cli.command("sort-log")
@click.argument("log_path", type=click.Path(exists=True))
@click.pass_obj
def sort_log(obj: dict, log_path: str) -> None:
    """Print sharpness-ranked images from a filter log."""
    from pathlib import Path
    from lora_pipeline.pipeline.sort_log import run
    run(Path(log_path))


@cli.command("all")
@click.pass_context
def run_all(ctx: click.Context) -> None:
    """Run the complete pipeline: download → filter → crop → dedupe → clip → generate → update-gallery → review."""
    ctx.invoke(download)
    ctx.invoke(filter)
    ctx.invoke(crop)
    ctx.invoke(dedupe)
    ctx.invoke(clip)
    ctx.invoke(generate)
    ctx.invoke(update_gallery)
    ctx.invoke(review)
