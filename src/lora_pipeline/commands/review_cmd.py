import webbrowser

from lora_pipeline.config import PipelineConfig
from lora_pipeline.commands import server


def run(cfg: PipelineConfig) -> None:
    server.start(cfg.dest)
    webbrowser.open("http://localhost:8000/gallery.html")
