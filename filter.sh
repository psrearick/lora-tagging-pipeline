#!/bin/bash

dirx="$(dirname -- $(readlink -fn -- "$0"; echo x))";
DIR="${dirx%x}";
cd "$DIR"

source "$DIR/env.conf"

echo "=== Filtering dataset ==="

python3 filter_dataset.py $DEST/raw $DEST/filtered \
    --min-width 1024 \
    --min-height 1024 \
    --sharpness-accept 80 \
    --sharpness-review 40

echo "=== Done ==="
