#!/bin/bash

echo "=== Filtering dataset ==="

python3 filter_dataset.py ~/dataset/test/raw ~/dataset/test/filtered \
    --min-width 1024 \
    --min-height 1024 \
    --sharpness-accept 80 \
    --sharpness-review 40

echo "=== Done ==="
