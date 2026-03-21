#!/usr/bin/env bash

dirx="$(dirname -- $(readlink -fn -- "$0"; echo x))";
DIR="${dirx%x}";
cd "$DIR"

source "$1"

for i in "${!SOURCES[@]}"; do
    src="${SOURCES[$i]}"
    echo "========================================="
    echo "Downloading: $src ($SORT)"
    echo "========================================="

    url="${DOWNLOAD_URL_TEMPLATE/\{source\}/$src}"
    url="${url/\{sort\}/$SORT}"

    gallery-dl \
        --download-archive "$ARCHIVE" \
        --destination "$DEST/raw" \
        --config "$GALLERY_CONF" \
        --range "$START-$END" \
        --chapter-range "$START-$END" \
        --filter "extension in ('jpg', 'jpeg', 'png', 'webp')" \
        "$url"

    if [[ $i -lt $(( ${#SOURCES[@]} - 1 )) ]]; then
        SLEEP_TIME=$(( 45 + RANDOM % 30 ))
        echo "Sleeping ${SLEEP_TIME}s before next subreddit..."
        sleep "$SLEEP_TIME"
    fi
done

echo ""
echo "All downloads complete."
echo "Archive: $ARCHIVE"
