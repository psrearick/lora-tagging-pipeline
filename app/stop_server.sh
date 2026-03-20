#!/bin/bash
PID_FILE=/tmp/http_server.pid
if [ -f "$PID_FILE" ]; then
    echo "$(cat $PID_FILE)"
    kill "$(cat $PID_FILE)" && rm "$PID_FILE"
    echo "Server stopped"
else
    echo "No PID file found — is the server running?"

    grep_res="$(pgrep -f "http.server")"

    if [[ -n $grep_res ]]; then
        echo "Possible Match: $grep_res"
    fi
fi
