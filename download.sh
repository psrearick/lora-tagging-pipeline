#!/usr/bin/env bash

dirx="$(dirname -- $(readlink -fn -- "$0"; echo x))";
DIR="${dirx%x}";
cd "$DIR"

source "$DIR/env.conf"

for sub in "${SUBREDDITS[@]}"; do
    echo "========================================="
    echo "Downloading: $sub/$SORT"
    echo "========================================="

    gallery-dl \
        --download-archive "$ARCHIVE" \
        --destination "$DEST/raw" \
        --config "$DIR/$GALLERY_CONF" \
        --range "$START-$END" \
        --chapter-range "$START-$END" \
        --filter "extension in ('jpg', 'jpeg', 'png', 'webp')" \
        "https://www.reddit.com/r/$sub/$SORT"
done

echo ""
echo "All downloads complete."
echo "Archive: $ARCHIVE"
