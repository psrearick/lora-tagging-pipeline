#!/usr/bin/env python3
"""
Generate a browser-based review gallery from clip_labels.json.
Usage: python3 make_gallery.py ~/dataset/clip_labels.json ~/dataset/gallery.html
"""
import json, sys
from pathlib import Path

labels_path = Path(sys.argv[1])
output_path = Path(sys.argv[2])

with open(labels_path) as f:
    results = json.load(f)

# Group by top bucket
from collections import defaultdict
by_bucket = defaultdict(list)
for r in results:
    by_bucket[r["top_bucket"]].append(r)

html = ['<!DOCTYPE html><html><head><meta charset="utf-8">',
        '<style>',
        'body{font-family:monospace;background:#111;color:#eee;margin:0;padding:16px}',
        'h2{color:#aaa;border-bottom:1px solid #333;padding-bottom:8px}',
        '.grid{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:32px}',
        '.card{width:200px;background:#222;border-radius:6px;overflow:hidden;cursor:pointer}',
        '.card img{width:100%;height:200px;object-fit:cover;display:block}',
        '.card .info{padding:6px;font-size:11px;color:#888}',
        '.card .score{color:#6cf;font-weight:bold}',
        '</style></head><body>']

for bucket in sorted(by_bucket.keys()):
    images = sorted(by_bucket[bucket], key=lambda x: x["top_score"], reverse=True)
    html.append(f'<h2>{bucket} ({len(images)} images)</h2><div class="grid">')
    for img in images:
        path = img["path"]
        score = img["top_score"]
        sub = img["subreddit"]
        html.append(
            f'<div class="card">'
            f'<img src="file://{path}" loading="lazy">'
            f'<div class="info">'
            f'<span class="score">{score:.3f}</span> · {sub}'
            f'</div></div>'
        )
    html.append('</div>')

html.append('</body></html>')

with open(output_path, "w") as f:
    f.write("\n".join(html))

print(f"Gallery written → {output_path}")
print("Open with: open " + str(output_path))
