#!/bin/bash

echo "=== Downloading from Reddit ==="

poetry run gallery-dl "https://www.reddit.com/r/pussy/top/?t=all" --range 1-300  \
    --filter "extension in ('jpg', 'jpeg', 'png', 'webp')"
poetry run gallery-dl "https://www.reddit.com/r/godpussy/top/?t=all" --range 1-300  \
    --filter "extension in ('jpg', 'jpeg', 'png', 'webp')"
poetry run gallery-dl "https://www.reddit.com/r/landingstripnsfw/top/?t=all" --range 1-300  \
    --filter "extension in ('jpg', 'jpeg', 'png', 'webp')"
poetry run gallery-dl "https://www.reddit.com/r/trimmedshavedbush/top/?t=all" --range 1-400  \
    --filter "extension in ('jpg', 'jpeg', 'png', 'webp')"
poetry run gallery-dl "https://www.reddit.com/r/pussyaddicts/top/?t=all" --range 1-300  \
    --filter "extension in ('jpg', 'jpeg', 'png', 'webp')"
poetry run gallery-dl "https://www.reddit.com/r/neatbush/top/?t=all" --range 1-300  \
    --filter "extension in ('jpg', 'jpeg', 'png', 'webp')"
poetry run gallery-dl "https://www.reddit.com/r/PussiesCloseUp/top/?t=all" --range 1-300  \
    --filter "extension in ('jpg', 'jpeg', 'png', 'webp')"
poetry run gallery-dl "https://www.reddit.com/r/PerfectPussy/top/?t=all" --range 1-300  \
    --filter "extension in ('jpg', 'jpeg', 'png', 'webp')"
poetry run gallery-dl "https://www.reddit.com/r/shavedpussies/top/?t=all" --range 1-300  \
    --filter "extension in ('jpg', 'jpeg', 'png', 'webp')"
poetry run gallery-dl "https://www.reddit.com/r/tidybush/top/?t=all" --range 1-300  \
    --filter "extension in ('jpg', 'jpeg', 'png', 'webp')"
poetry run gallery-dl "https://www.reddit.com/r/youngpussylips/top/?t=all" --range 1-300  \
    --filter "extension in ('jpg', 'jpeg', 'png', 'webp')"
poetry run gallery-dl "https://www.reddit.com/r/Hairy_Trimmed_Pussy/top/?t=all" --range 1-300  \
    --filter "extension in ('jpg', 'jpeg', 'png', 'webp')"
poetry run gallery-dl "https://www.reddit.com/r/TeenPussyGW/top/?t=all" --range 1-300  \
    --filter "extension in ('jpg', 'jpeg', 'png', 'webp')"
poetry run gallery-dl "https://www.reddit.com/r/TightPussyGirls/top/?t=all" --range 1-300  \
    --filter "extension in ('jpg', 'jpeg', 'png', 'webp')"
poetry run gallery-dl "https://www.reddit.com/r/needypussy/top/?t=all" --range 1-300  \
    --filter "extension in ('jpg', 'jpeg', 'png', 'webp')"

echo "=== Filtering dataset ==="

python3 filter_dataset.py ~/dataset/raw ~/dataset/sorted \
    --min-width 900 \
    --min-height 768 \
    --sharpness-accept 80 \
    --sharpness-review 40

echo "=== Done ==="
read -p "Press enter to continue"
