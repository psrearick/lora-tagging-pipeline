#!/usr/bin/env bash

dirx="$(dirname -- $(readlink -fn -- "$0"; echo x))";
DIR="${dirx%x}";
cd "$DIR"

source "$1"

for src in "${SOURCES[@]}"; do
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
done

echo ""
echo "All downloads complete."
echo "Archive: $ARCHIVE"
