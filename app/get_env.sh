#!/bin/bash

CUR="$(pwd)"

if [[ "$1" = "--config" ]]; then
    shift
    config="$1"
fi

if [[ ! -f "$config" ]]; then
    config="$CUR/$config"
fi

if [[ ! -f "$config" ]]; then
    exit 1
fi

if [[ "$path_var" == /* ]]; then
    echo "$config"
else
    echo "$(readlink -f $config)"
fi
