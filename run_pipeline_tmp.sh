#!/bin/bash

echo "=== Downloading from Reddit ==="

gallery-dl "https://www.reddit.com/r/ruinedorgasms/top/?t=all" --range 1-300  \
    --filter "extension in ('jpg', 'jpeg', 'png', 'webp')"


gallery-dl -K "https://www.reddit.com/r/RuinedOrgasms/comments/r4o439/benefits_of_chastity_not_only_can_i_get_the_thick/"
