#!/bin/bash
PID_FILE=/tmp/http_server.pid
if [ -f "$PID_FILE" ]; then
    kill "$(cat $PID_FILE)" && rm "$PID_FILE"
    echo "Server stopped"
else
    echo "No PID file found — is the server running?"
fi
