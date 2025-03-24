#!/bin/bash

OD="$PWD"

pushd "$1" > /dev/null

SUBTITLES="subtitles='subtitles.srt':force_style='FontName=Arial,Bold=1,FontSize=18,TextStyle=Bold,PrimaryColour=&H00FFFFFF,BackColour=&HFF000000,BorderStyle=3,Outline=2,MarginV=15%,MarginL=5%,MarginR=5%'"
DURATION="$(ffprobe -i audio.wav -show_entries format=duration -v quiet -of csv="p=0")"

if [[ $DURATION -lt 60 ]]; then
  DURATION=$((DURATION + 1))
fi

RCLIP=
if [[ "$2" == "--random-clip" ]]; then
    RCLIP="$(find $OD/clips -type f | shuf -n 1)"
fi


if [[ "$2" == "--random-clip" ]]; then
    ffmpeg \
        -y \
        -r 60 \
        -i "$RCLIP" \
        -i "audio.wav" \
        -c:v libx264 \
        -vf "$SUBTITLES" \
        -t "$DURATION" \
        output.mp4
else
    ffmpeg \
        -hwaccel cuda \
        -hwaccel_output_format cuda \
        -loop 1 \
        -y \
        -r 60 \
        -i "images"/* \
        -i "audio.wav" \
        -filter_complex "[0:v]scale=2000:2000,zoompan=z='zoom+0.00003':d=2000:x='iw/2-(iw/zoom)/2 + sin(time/10)*5':y='ih/2-(ih/zoom)/2 + cos(time/10)*5',$SUBTITLES,scale=1080:1920,tblend=all_mode=average,setpts=PTS-STARTPTS[v];[1:a]aloop=loop=150[a]" \
        -map "[v]" \
        -map "[a]" \
        -c:v h264_nvenc \
        -preset p1 \
        -t $DURATION \
        -s 1080x1920 \
        output.mp4
fi

popd > /dev/null