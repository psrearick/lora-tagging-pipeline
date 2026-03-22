import random
import subprocess
import time

from lora_pipeline.config import PipelineConfig


def run(cfg: PipelineConfig) -> None:
    dest_raw = cfg.dest / "raw"
    dest_raw.mkdir(parents=True, exist_ok=True)

    for i, source in enumerate(cfg.sources):
        url = cfg.download_url_template.replace("{source}", source).replace("{sort}", cfg.sort)
        print("=========================================")
        print(f"Downloading: {source} ({cfg.sort})")
        print("=========================================")

        cmd = [
            "gallery-dl",
            "--download-archive", str(cfg.archive),
            "--destination", str(dest_raw),
            "--config", str(cfg.gallery_conf),
            "--range", f"{cfg.start}-{cfg.end}",
            "--chapter-range", f"{cfg.start}-{cfg.end}",
            "--filter", "extension in ('jpg', 'jpeg', 'png', 'webp')",
            url,
        ]
        subprocess.run(cmd, check=True)

        if i < len(cfg.sources) - 1:
            sleep_time = random.randint(45, 74)
            print(f"Sleeping {sleep_time}s before next source...")
            time.sleep(sleep_time)

    print("")
    print("All downloads complete.")
    print(f"Archive: {cfg.archive}")
