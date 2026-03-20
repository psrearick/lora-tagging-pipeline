#!/bin/bash

CUR="$(pwd)"

dirx="$(dirname -- $(readlink -fn -- "$0"; echo x))";
DIR="${dirx%x}";
cd "$DIR"

source "$DIR/sources.conf"

CROP="$DEST/cropped"
LABELS="$DEST/clip_labels.json"

function download() {
    "$CUR/download.sh"
}

function filter() {
    "$CUR/filter.sh"
}

function crop() {
    poetry run python "$CUR/smart_crop.py" "$DEST/sorted/accepted" "$CROP"
}

function dedupe() {
    poetry run python "$CUR/dedupe.py" "$CROP"
}

function clip() {
    poetry run python "$CUR/clip_label.py" "$CROP" "$LABELS"
}

function generate() {
    poetry run python "$CUR/generate_data.py" "$LABELS" "$DEST/data.json"
}

function open_gallery() {
    open http://localhost:8000/gallery.html
}

function stop() {
    "$CUR/stop_server.sh"
}

function start() {
    "$CUR/start_server.sh"
}

function review() {
    start
    wait 2
    open
}

function export_training() {
    echo ""
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
        # Shift the arguments so $1 within the function refers to the name, not the command
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

cd "$CUR"
