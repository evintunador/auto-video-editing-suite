# video-silence-remover

This repo takes a .mov video from quicktime and removes silent portions as a quick and easy way to edit awkward silences out of videos. I use it for my youtube channel https://www.youtube.com/channel/UCeQhm8DwHBg_YEYY0KGM1GQ

## Repo Contents

- `silence-remover.py` - does everything. Call it 
- `config.py` - this will let you edit the settings, silence threshold and buffer time

## SETUP

1. Clone the repository to your local machine.
2. Install the required Python packages by running `pip install -r requirements.txt` in your terminal.

## USAGE

1. Run the `silence-remover.py` script with `input_video.mov` and `output_video.mov` 

## NOTE

The script is not designed to handle errors or be generally useable past what I need it for. But if you have an edit you'd like to make feel free to do so, and as long as it doesn't make the day-to-day implementation more comlicated for me then I'll merge it. 