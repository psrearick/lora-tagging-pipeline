from lora_pipeline.config import PipelineConfig
from lora_pipeline.pipeline.smart_crop import crop_directory


def run(cfg: PipelineConfig) -> None:
    input_dir  = cfg.dest / "filtered" / "accepted"
    output_dir = cfg.dest / "cropped"
    crop_directory(input_dir, output_dir, target=1024)
