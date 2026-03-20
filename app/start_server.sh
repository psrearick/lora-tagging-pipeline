#!/bin/bash

DEST="$1"

PID_FILE=/tmp/http_server.pid

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        echo "Server is already running (PID $PID)"
        exit 1
    else
        echo "Stale PID file found, cleaning up..."
        rm "$PID_FILE"
    fi
fi

cd "$DEST"
python3 -m http.server 8000 &
echo $! > "$PID_FILE"
echo "Server started (PID $(cat $PID_FILE))"
