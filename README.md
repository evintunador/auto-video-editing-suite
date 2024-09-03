# auto-video-editing-suite

This repo contains all the tools that allow me to never ever open up an actual video editor, thereby saving me HELLA time. Here's a quick rundown:
- `silence_remover.py` removes silent portions
- `timestamps.py` allows for the recording of youtube-style timestamps during the actual video using a simple hotkey
- `concatenator.py` takes as input multipl evideo files and stitches them together in the order they were provided

## setup
1. Clone the repository to your local machine.
2. Create a virtual environment and install the required Python packages.
	- You might need to install ffmpeg separately from regular python packages. On mac if you have homebrew that's `brew install ffmpeg`
3. *BONUS:* If you'd prefer an app icon that you can just click instead of terminal commands, change the file path in `launch_silence_remover.sh` and `launch_concatenator.sh` to your own project's file path on your system, make the .sh files executable, and create an app shortcut for them. I'll let you ask chatGPT how to do that

## usage
If you want to use the core scripts as opposed to their GUI versions, i'll let you open them up and read through the arguments to figure that out.

### silence remover
Run `python silence_remover_gui.py` to see a GUI with a bunch of settings that'll let you pick:
- the file to remove silences from (must be .mp4)
- a timestamps file that needs to be adjusted to account for the silence removing (must be .txt in the youtube style; see `timestamps_example.txt`)
- where to save the output video and timestamp files
- the decibel threshold for silence removal. audio below this value will be considered "silence". Yes ik having a negative number is weird but that's how decibels work. suggested range is bw -50 to -40 depending on your microphone and background noise 
- the chunk duration is a parameter designed to help not destroy your RAM. basically before removing silences the script will cut the video up into chunks, and this parameter defines how long these chunks should be (in seconds). I've got 8gb of ram and 150 seconds works for me; if you've got more you can do larger chunk sizes. In theory you want larger chunk sizes in order to avoid the rare but potential issue of very short silent portions near the chunk border not being properly removed, but honestly i've yet to notice this as an actual issue
- the minimum silence length is the minimum number of seconds that a silent portion has to last for it to actually be counted and therefore removed. The reason this has to exist is to allow for the natural short silences that occur in between words while talking.
- the buffer duration is there because when you're talking you don't suddenly switch from loud to quiet, it actually takes a few milliseconds for the volume to fall. If we were to just cut that falling period at the point where it went below the decibel threshold, we'd end up with audio that sounds very choppy. in order to avoid that, i've added on a small buffer period (default 0.2 seconds) of audio that would otherwise count as silence around every loud portion. if the cuts sound choppy to you, consider making this buffer period longer

### concatenator
If you've got multiple video files you want to combine back-to-back and you're too lazy to open a full video editing software, run `python video_concatenator_gui.py` and it'll bring up a GUI that'll let you
- pick video files (.mp4) and their ordering
- pick corresponding timestamp (.txt) files. If a given video in the sequence doesn't have a corresponding timestamp file, you need to hit the "add a placeholder" button and position that entry to match the timestamp-less video. If none of your videos have timestamp files, just ignore that whole part of the app
- select the output video file's path
- select the output timestamp file's path (defaults to `{path/to/video_name}_timestamps.txt`)

### timestamps recorder
1. Run `python timestamps.py` before you start recording 
2. At the moment you hit record, simultaneously hit the hotkey (defaults to `=`) to start the timer and creat the first "0:00 Intro" timestamp. 
3. for every time you want to set a new timestamp just hit the hotkey again
4. When you're finished with the video hit the `Esc` key to end the script. It's no biggie if you forget to do this until awhile later since hitting this key doesn't record a timestamp; i usually hit it multiple minutes after i've actually finished recording
5. The timestamps will be saved to `timestamps.txt`. Be careful about overwriting previous timestamps files since there's no way to configure where this gets saved to each time

## NOTES
- I use this repo for my youtube channel [@Tunadorable](https://www.youtube.com/channel/UCeQhm8DwHBg_YEYY0KGM1GQ), go check it out
- I originally had the idea for the silence remover and when I searched for it online I found https://github.com/carykh/jumpcutter but their version was hella glitchy for me so I just wrote it from scratch. Also wtf is with them charging $100 for the app version of that script, I tried the free trial and that thing didn't even work either