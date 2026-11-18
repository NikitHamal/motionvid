#!/bin/bash
# Sequential build queue (2 GB box: one render at a time). Usage: scripts/queue.sh id1 id2 ...
cd "$(dirname "$0")/.."
export PYTHONPATH=src
for i in "$@"; do python3 scripts/build_demos.py "$i" > "out/build_$i.log" 2>&1; echo "$i done $(date +%T)" >> out/queue.log; done
