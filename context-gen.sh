#!/bin/bash
set -e
cd "$(dirname "$(readlink -f "$0")")"
python3 main.py "$@" --log-file "output/log.txt"
