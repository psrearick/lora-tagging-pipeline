#!/usr/bin/env bash

CUR="$(pwd)"

dirx="$(dirname -- $(readlink -fn -- "$0"; echo x))";
DIR="${dirx%x}";
cd "$DIR"

source "$DIR/sources.conf"

for sub in "${SUBREDDITS[@]}"; do
    echo "========================================="
    echo "Downloading: $sub/$SORT"
    echo "========================================="

    gallery-dl \
        --download-archive "$ARCHIVE" \
        -d "$DEST" \
        --range "$START-$END" \
        --chapter-range "$START-$END" \
        --filter "extension in ('jpg', 'jpeg', 'png', 'webp')" \
        "https://www.reddit.com/r/$sub/$SORT"
done

echo ""
echo "All downloads complete."
echo "Archive: $archive"

cd "$CUR"
