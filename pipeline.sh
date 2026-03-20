#!/bin/bash

dirx="$(dirname -- $(readlink -fn -- "$0"; echo x))";
DIR="${dirx%x}";
cd "$DIR"

source "$DIR/env.conf"

CROP="$DEST/cropped"
LABELS="$DEST/clip_labels.json"

function download() {
    "$DIR/download.sh"
}

function filter() {
    "$DIR/filter.sh"
}

function crop() {
    poetry run python "$DIR/smart_crop.py" "$DEST/sorted/accepted" "$CROP"
}

function dedupe() {
    poetry run python "$DIR/dedupe.py" "$CROP"
}

function clip() {
    poetry run python "$DIR/clip_label.py" "$CROP" "$LABELS"
}

function generate() {
    poetry run python "$DIR/generate_data.py" "$LABELS" "$DEST/data.json"
}

function open_gallery() {
    open http://localhost:8000/gallery.html
}

function stop() {
    "$DIR/stop_server.sh"
}

function start() {
    "$DIR/start_server.sh"
}

function review() {
    start
    wait 2
    open_gallery
}

function export_training() {
    if [[ -n "$LORA_CONFIG" ]]
    then
        poetry run python "$DIR/export_training.py" "$DEST/training" --group-by-lora "$LORA_CONFIG"
    else
        poetry run python "$DIR/export_training.py" "$DEST/training" --group-by-lora
    fi
}

function update_gallery() {
    cp gallery.html "$DEST/gallery.html"
}

function all() {
    download
    filter
    crop
    dedupe
    clip
    generate
    review
}

function usage() {
    echo "Usage: ./pipeline.sh [download|filter|crop|dedupe|clip|generate|review|export_training|start|stop|all]"
    exit 1
}

case "$1" in
    download)
        shift
        download
        ;;
    filter)
        shift
        filter
        ;;
    crop)
        shift
        crop
        ;;
    dedupe)
        shift
        dedupe
        ;;
    clip)
        shift
        clip
        ;;
    generate)
        shift
        generate
        ;;
    open)
        shift
        open_gallery
        ;;
    review)
        shift
        review
        ;;
    export)
        shift
        export_training
        ;;
    start)
        shift
        start
        ;;
    stop)
        shift
        stop
        ;;
    all)
        shift
        all
        ;;
    update-gallery)
        shift
        update_gallery
        ;;
    *)
        usage
        ;;
esac
