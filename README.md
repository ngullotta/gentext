# GenText

Automatically create consumable videos from 4chan greentext stories

## Installation
First you will need tesseract installed (use your distros package manager) and cuda-toolkit

```shell
$ git clone ...
$ cd gentext
$ poetry install
```

On Fedora I have to set my .env as such
```
LD_LIBRARY_PATH="/home/muto/src/personal/greentext/.venv/lib/python3.11/site-packages/nvidia/cusparse/lib:/home/muto/src/personal/greentext/.venv/lib/python3.11/site-packages/nvidia/nccl/lib:/home/muto/src/personal/greentext/.venv/lib/python3.11/site-packages/nvidia/cudnn/lib"
OPEN_AI_KEY="<snip>"
```

## Usage:
```shell
$ python main.py greentexts/image.png
```

Once done you will see output in the `output/scripts/` folder for your movie

If you're happy with the output, run:
```shell
$ ./export.sh output/scripts/<your new script>
```

This will combine all the parts to make the video