1. `run_pipeline.sh`
2. sort: `poetry run python sort_log.py ~/dataset/sorted/filter_log.jsonl`
3. dedupe: `poetry run python dedupe.py ~/dataset/sorted/accepted`
4. label: `poetry run python clip_label.py ~/dataset/sorted/accepted ~/dataset/clip_labels.json`
5. reorganize: `poetry run python reorganize_by_bucket.py ~/dataset/clip_labels.json ~/dataset/by_bucket`
6. generate gallery: `poetry run python make_gallery.py ~/dataset/clip_labels.json ~/dataset/gallery.html`
7. manual pass: `open ~/dataset/gallery.html`
