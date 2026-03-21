#!/bin/bash


dirx="$(dirname -- $(readlink -fn -- "$0"; echo x))"
DIR="${dirx%x}"

CONFIG="$(echo $($DIR/get_env.sh "$@"))"

if [[ ! -n "$CONFIG" ]]; then
    echo "Config file not found"
    exit 1
fi

shift;shift

cd "$DIR"

source "$CONFIG"

CROP="$DEST/cropped"
LABELS="$DEST/clip_labels.json"

function download() {
    "$DIR/download.sh" "$CONFIG"
}

function filter() {
    "$DIR/filter.sh" "$CONFIG"
}

function crop() {
    poetry run python "$DIR/smart_crop.py" "$DEST/filtered/accepted" "$CROP"
}

function dedupe() {
    poetry run python "$DIR/dedupe.py" "$CROP"
}

function clip() {
    poetry run python "$DIR/clip_label.py" "$CROP" "$LABELS" --config "$LORA_CONFIG"
}

function generate() {
    poetry run python "$DIR/generate_data.py" "$LABELS" "$DEST/data.json" --config "$LORA_CONFIG"
}

function open_gallery() {
    open http://localhost:8000/gallery.html
}

function stop() {
    "$DIR/stop_server.sh"
}

function start() {
    "$DIR/start_server.sh" "$DEST"
}

function review() {
    start
    open_gallery
}

function export_training() {
    poetry run python "$DIR/export_training.py" "$DATA_FILE" "$DEST" --config "$LORA_CONFIG" --group-by-lora
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
    update_gallery
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
