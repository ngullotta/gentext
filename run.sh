#!/bin/sh

poetry shell

for file in "$@"; do
    TMPDIR="$(mktemp -d)"

    python main.py "$file" --output "$TMPDIR"

    SCRIPT_NAME="$(basename $(find "$TMPDIR/scripts/" -mindepth 1 -maxdepth 3 -type d))"

    echo "Script: $SCRIPT_NAME"

    ./export.sh "$TMPDIR/scripts/$SCRIPT_NAME" --random-clip

    python upload.py "$TMPDIR/scripts/$SCRIPT_NAME/"

    cp -r "$TMPDIR/scripts/$SCRIPT_NAME" output/scripts/ && rm -rf "$TMPDIR"

    sleep 60
done