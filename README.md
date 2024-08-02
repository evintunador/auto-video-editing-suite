# video-silence-remover

`silence_remover.py` takes a .mp4 video and removes silent portions as a quick and easy way to edit awkward silences out of videos. Personally it's the only video editing I do but you may want to use it as a pre-processing stage to save you time before real video editing.

## USAGE

1. Clone the repository to your local machine.
2. Install the required Python packages by running `pip install -r requirements.txt` in your terminal.
3. Install ffmpeg. On mac if you have homebrew that's `brew install ffmpeg`
3. Run `python silence_remover.py -h` to seea  list of optional arguments to tweak
4. Run `python silence_remover.py "path/to/video/file/input.mp4"` to trim silences from a video. By default the new video will be named/placed `path/to/video/file/input_no_silence.mp4`. If you've got a .txt file containing youtube timestamps in the following format then you can also input that into this script using `-t path/to/timestamps.txt` and the script will spit out `path/to/timestamps_adjusted.txt` with the newly adjusted times. Format:
```txt
0:00 string one
1:23 string two
45:67 string three
89:10 etc
```
2. Be annoyed by the excessive terminal output of ffmpeg
3. Enjoy your shittily edited video 

 ## NOTES
- I use it for my youtube channel [@Tunadorable](https://www.youtube.com/channel/UCeQhm8DwHBg_YEYY0KGM1GQ go check it out)
- I originally had the idea and when I searched for it online I found https://github.com/carykh/jumpcutter but their version was hella glitchy for me so I just wrote it from scratch. Also wtf is with them charging $100 for the app version of that script, I tried the free trial and that thing didn't even work either
- There's also `video_concatenator.py` which is what it sounds like, a simple script that takes the path to any number of mp4's as input and concatenates them in the order that you provided. obvi i really hate opening up a real video editor
```
python concatenator.py "path/to/first/video/file/input.mp4" "path/to/second/video/file/input.mp4" "path/to/third/video/file/input.mp4" "path/to/first/etc/input.mp4" "path/to/output.mp4"
```