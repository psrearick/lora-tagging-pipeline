#!/bin/bash

echo "=== Downloading from Reddit ==="

gallery-dl "https://www.reddit.com/r/pussy/top/?t=all" --range 1-300  \
    --filter "extension in ('jpg', 'jpeg', 'png', 'webp')"
