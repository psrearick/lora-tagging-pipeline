1. `run_pipeline.sh`
2. filter: `poetry run python filter_dataset.py ~/dataset/raw ~/dataset/sorted --min-height 1024 --min-width 1024`
<!-- 2. filter: `poetry run python filter_dataset.py ~/dataset/raw ~/dataset/sorted --sharpness-accept 100 --min-height 1024 --min-width 1024` -->
1. dedupe: `poetry run python dedupe.py ~/dataset/sorted/accepted`
2. label: `poetry run python clip_label.py ~/dataset/sorted/accepted ~/dataset/clip_labels.json`
3. reorganize: `poetry run python reorganize_by_bucket.py ~/dataset/clip_labels.json ~/dataset/by_bucket`
4. generate data: `poetry run python generate_data.py ~/dataset/clip_labels.json ~/dataset/data.json`
5. copy gallery: `cp gallery.html ~/dataset/gallery.html`
6. serve gallery: `cd ~/dataset && python3 -m http.server 8000`
7. open gallery: `open http://localhost:8000/gallery.html`
