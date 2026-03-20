1. `run_pipeline.sh`
2. filter: `poetry run python filter_dataset.py ~/dataset/raw ~/dataset/sorted --min-height 1024 --min-width 1024`
3. crop: `poetry run python smart_crop.py ~/dataset/sorted/accepted ~/dataset/cropped`
4. dedupe: `poetry run python dedupe.py ~/dataset/cropped`
5. label: `poetry run python clip_label.py ~/dataset/cropped ~/dataset/clip_labels.json`
    <!-- 6. reorganize: `poetry run python reorganize_by_bucket.py ~/dataset/clip_labels.json ~/dataset/by_bucket` -->
6. generate data: `poetry run python generate_data.py ~/dataset/clip_labels.json ~/dataset/data.json`
7. copy gallery: `cp gallery.html ~/dataset/gallery.html`
8. serve gallery: `cd ~/dataset && python3 -m http.server 8000`
9.  open gallery: `open http://localhost:8000/gallery.html`
