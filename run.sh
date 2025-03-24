#!/bin/sh

poetry shell

for file in "$@"; do
    TMPDIR="$(mktemp -d)"

    python main.py "$file" --output "$TMPDIR"

    SCRIPT_NAME="$(basename $(find "$TMPDIR/scripts/" -mindepth 1 -maxdepth 3 -type d))"

    echo "Script: $SCRIPT_NAME"

    ./export.sh "$TMPDIR/scripts/$SCRIPT_NAME" --random-clip

    python upload.py "$TMPDIR/scripts/$SCRIPT_NAME/"

    cp -r "$TMPDIR/scripts/$SCRIPT_NAME" output/scripts/

    cp "$TMPDIR/scripts/$SCRIPT_NAME/output.mp4" "TiktokAutoUploader/VideosDirPath/$SCRIPT_NAME.mp4"

    # pushd "TiktokAutoUploader" > /dev/null

    # COOKIE="CookiesDir/tiktok_session-anontalks.cookie"
    # if [[ $(find "$COOKIE" -mtime +1 -print) ]]; then
    #     echo "Cookie exists and is older than 1 day"
    #     rm -rf "$COOKIE"
    #     python cli.py login -n anontalks
    # fi

    # title="$(jq < "$TMPDIR/scripts/$SCRIPT_NAME/script.json" .title)"
    # title="${title:1:-1}"
    # python cli.py upload --users anontalks -v "$SCRIPT_NAME.mp4" -t "$title #fyp #4chan #greentext #funny #weird #horror"

    # popd > /dev/null

    rm -rf "$TMPDIR"

    sleep 60
done