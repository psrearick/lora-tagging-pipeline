from lora_pipeline.config import PipelineConfig
from lora_pipeline.pipeline.dedupe import run as run_dedupe


def run(cfg: PipelineConfig) -> None:
    run_dedupe(cfg.dest / "cropped")
