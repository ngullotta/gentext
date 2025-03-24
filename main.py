import argparse
import datetime
import json
import os
import pathlib
import shutil
import subprocess

import openai
import PIL
import pytesseract
import torch
import whisper
from PIL import Image, ImageFilter
from pydub import AudioSegment
from pydub.silence import split_on_silence
from TTS.api import TTS

parser = argparse.ArgumentParser("GenText")
parser.add_argument(
    "files",
    nargs="+",
    type=pathlib.Path,
    help="Story images or text files to parse",
)
parser.add_argument("--no-cleanup", action="store_true", default=False)
parser.add_argument("--no-tts", action="store_true", default=False)
parser.add_argument(
    "-o", "--output", type=pathlib.Path, default=pathlib.Path("output")
)
parser.add_argument(
    "-m",
    "--tts-model",
    default="tts_models/multilingual/multi-dataset/xtts_v2",
)
parser.add_argument(
    "-s",
    "--tts-speaker",
    default="Craig Gutsy",
)

CLEAN_PROMPT = """
You are a helper who cleans up tesseract parsed 4chan greentext stories so that a TTS engine can read them properly.
I need the TTS to be able to read this in 60 seconds or less so paraphrase long-winded sections while keeping the main story beats intact
Do remove extraneous information like dates, the "anonymous" ID or post numbers.
Do remove sections not relevant to the overall story
Do include a small snippet at the begining that says "Anonymous writes on (date):"
"""


def tess_read(image: PIL.Image) -> str:
    return pytesseract.image_to_string(image)


def ai_prompt(s: str, prompt: str = CLEAN_PROMPT) -> str:
    if (key := os.environ.get("OPEN_AI_KEY")) is None:
        print("Cannot clean text, OPEN_AI_KEY is empty")
        return s
    client = openai.OpenAI(api_key=key)
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "developer", "content": prompt},
            {
                "role": "user",
                "content": s,
            },
        ],
    )
    return completion.choices[0].message.content


def cleanup_audio(
    path: pathlib.Path,
    trim_silence: bool = True,
    speedup: bool = True,
    until_length: int = 60,
) -> None:
    sound = AudioSegment.from_file(str(path.resolve()), format=path.suffix[1:])

    if sound.duration_seconds <= 60:
        return

    if trim_silence:
        trimmed = AudioSegment.empty()
        audio_chunks = split_on_silence(
            sound, min_silence_len=50, silence_thresh=-45, keep_silence=50
        )
        # Putting the file back together
        for chunk in audio_chunks:
            trimmed += chunk
        sound = trimmed

    if sound.duration_seconds <= 60:
        return

    if speedup:
        factor = min(sound.duration_seconds / until_length, 1.5)
        sound = sound.speedup(playback_speed=factor)

    if sound.duration_seconds > 60:
        delta = abs(sound.duration_seconds - until_length)
        print(f"Warning: Failed to reach target length by {delta}s")

    sound.export(str(path.resolve()), format=path.suffix[1:])


def generate_tts(
    text: str, model: str, speaker: str, outpath: str = "/tmp/output.wav"
) -> pathlib.Path:
    device = "cuda" if torch.cuda.is_available() else "cpu"
    tts = TTS(model).to(device)
    print("Generating tts audio...")
    tts.tts_to_file(
        text=text, speaker=speaker, language="en", file_path=outpath
    )
    print("Done")
    path = pathlib.Path(outpath)
    cleanup_audio(path)
    return path


def process_image(image_path, output_path, crop_percentage=0.5):
    """
    Crops the right side, zooms to increase vertical height, and calculates the blurred background
    before cropping to avoid black bars.
    """
    try:
        img = Image.open(image_path)
    except FileNotFoundError:
        print(f"Error: Image not found at {image_path}")
        return

    target_width, target_height = 1080, 1920
    img_width, img_height = img.size

    # Calculate blurred background before crop
    blurred_img = img.filter(ImageFilter.GaussianBlur(radius=30))
    blurred_img = blurred_img.resize(
        (target_width, target_height), Image.Resampling.LANCZOS
    )

    # Crop the right side
    crop_width = int(img_width * crop_percentage)
    img = img.crop((0, 0, img_width - crop_width, img_height))
    img_width = img.size[0]

    # Calculate the vertical increase from the cropped space
    vertical_increase = int(crop_width * (target_height / target_width))

    # Increase vertical height by adding transparent pixels
    new_height = img_height + vertical_increase
    new_img = Image.new("RGBA", (img_width, new_height), (0, 0, 0, 0))
    top_offset = vertical_increase // 2
    new_img.paste(img, (0, top_offset))
    # img = new_img.convert("RGB")
    img_width, img_height = img.size

    # Calculate aspect ratios and resize
    img_aspect = img_width / img_height
    target_aspect = target_width / target_height

    if img_aspect > target_aspect:
        new_width = target_width
        new_height = int(target_width / img_aspect)
    else:
        new_height = target_height
        new_width = int(target_height * img_aspect)

    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

    # Create a new image with the target dimensions
    final_img = Image.new("RGB", (target_width, target_height))

    # Paste the blurred background
    final_img.paste(blurred_img, (0, 0))

    # Calculate paste position for the original image
    paste_x = (target_width - img.width) // 2
    paste_y = (target_height - img.height) // 2

    # Paste the original image onto the blurred background
    final_img.paste(img, (paste_x, paste_y))

    # Save the formatted image
    final_img.save(output_path)


MOOD_TO_BACKING_TRACKS = {
    "spooky": {
        "file": "spooky.mp3",
        "attribution": "jazz_music_loop.mp3 by NikoSardas -- https://freesound.org/s/456797/ -- License: Attribution 4.0",
    },
    "mysterious": {
        "file": "spooky.mp3",
        "attribution": "jazz_music_loop.mp3 by NikoSardas -- https://freesound.org/s/456797/ -- License: Attribution 4.0",
    },
    "funny": {
        "file": "funny.mp3",
        "attribution": "Bright and Fun Upbeat Joy by LolaMoore -- https://freesound.org/s/759605/ -- License: Attribution 4.0",
    },
}

if __name__ == "__main__":
    args = parser.parse_args()
    for file in args.files:
        data = ""
        if file.suffix in [".png", ".jpeg"]:
            img = PIL.Image.open(file)
            data = tess_read(img)

            if args.no_cleanup is False:
                data = ai_prompt(data)

        if file.suffix in [".txt"]:
            data = file.read_text()

        if len(data) == 0:
            print("No usuable data for story")
            continue

        outpath = args.output / file.with_suffix(".txt").name
        if outpath != file:
            with open(outpath, "w") as fp:
                fp.write(data)

        if args.no_tts:
            tts_file = pathlib.Path("/tmp/output.wav")
        else:
            tts_file = generate_tts(data, args.tts_model, args.tts_speaker)

        PROMPT = (
            "In one word, give a genre for this short story. Valid options are: "
            + ", ".join(MOOD_TO_BACKING_TRACKS.keys())
        )
        mood = ai_prompt(data, PROMPT).lower()
        mood_audio_path = pathlib.Path(
            f"backing-tracks/{MOOD_TO_BACKING_TRACKS[mood]['file']}"
        )
        backing = AudioSegment.from_file(
            str(mood_audio_path.resolve()),
            format=mood_audio_path.suffix[1:],
        )

        narration = AudioSegment.from_file(
            str(tts_file.resolve()), format="wav"
        )
        backing = backing - 7
        combined = narration.overlay(backing, position=0, loop=True)

        title = ai_prompt(
            data,
            prompt='Pick a quick title for this. Don\'t include any characters other than alphanumeric chars and spaces. Include the author in the title: "Anon", like "Anon\'s experience"',
        ).replace('"', "")
        script = {
            "title": title,
            "mood": mood,
            "text": data,
            "attributions": MOOD_TO_BACKING_TRACKS[mood]["attribution"],
        }

        # Write asset bundle
        movie = (
            args.output
            / "scripts"
            / title.lower().replace(" ", "_").replace("'", "")
        )
        movie.mkdir(parents=True)
        combined.export(movie / "audio.wav", format="wav")
        with open(movie / "script.json", "w") as fp:
            fp.write(json.dumps(script, indent=4))

        images = movie / "images"
        images.mkdir(parents=True)

        for f in pathlib.Path("greentexts").iterdir():
            if f.stem == file.stem:
                process_image(
                    str(f), str(images / f.name), crop_percentage=0.35
                )

        # Generate srt
        def format_timestamp(seconds: float):
            milliseconds = int(seconds * 1000) % 1000
            seconds = int(seconds) % 60
            minutes = int(seconds / 60) % 60
            hours = int(seconds / 3600)
            return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"

        def generate_srt(audio_path, srt_path):
            model = whisper.load_model("base")
            result = model.transcribe(audio_path, verbose=False)

            with open(srt_path, "w", encoding="utf-8") as srt_file:
                for i, segment in enumerate(result["segments"]):
                    start_time = format_timestamp(segment["start"])
                    end_time = format_timestamp(segment["end"])
                    text = segment["text"].strip()
                    srt_file.write(f"{i+1}\n")
                    srt_file.write(f"{start_time} --> {end_time}\n")
                    srt_file.write(f"{text}\n\n")

        generate_srt(str(tts_file.resolve()), str(movie / "subtitles.srt"))
