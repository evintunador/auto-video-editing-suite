# video-silence-remover

`silence_remover.py` takes a .mp4 video and removes silent portions as a quick and easy way to edit awkward silences out of videos. Personally it's the only video editing I do but you may want to use it as a pre-processing stage to save you time before real video editing.

## USAGE

1. Clone the repository to your local machine.
2. Create a virtual environment and install the required Python packages by running `pip install -r requirements.txt` in your terminal.
	- You might need to install ffmpeg separately. On mac if you have homebrew that's `brew install ffmpeg`
3. Run `python silence_remover_gui.py` to see a GUI with a bunch of settings that'll let you pick the file to remove silences from and where to save it to. See `timestamps.txt` for an example of the format
4. *BONUS:* If you've got multiple video files you want to combine back-to-back and you're too lazy to open a full video editing software, run `python concatenator.py` and it'll bring up a GUI that'll let you pick files and their order. Obviously I really hate opening up a real video editor :P
- *BONUS^2:* Run `timestamps.py` before you start recording if you'd like to keep track of your timestamps as you record, which works very well in combination with using `silence_remover.py` as your only video editor. At the moment you hit record you should also hit the hotkey (\`) to start the timer and creat the first "0:00 Intro" timestamp. Then for every time you want to set a new timestamp just hit the hotkey again. Later when using the silence remover just select `timestamps.txt` and the script will automatically adjust the times to match the newly removed silent portions.
- *BONUS^3:* If you'd prefer an app icon that you can just click instead of terminal commands, change the file path in `launch_silence_remover.sh` and `launch_concatenator.sh` to your own project's file path on your system, make the .sh files executable, and create an app shortcut for them. I'll let you ask chatGPT how to do that

 ## NOTES
- I use it for my youtube channel [@Tunadorable](https://www.youtube.com/channel/UCeQhm8DwHBg_YEYY0KGM1GQ) go check it out
- I originally had the idea and when I searched for it online I found https://github.com/carykh/jumpcutter but their version was hella glitchy for me so I just wrote it from scratch. Also wtf is with them charging $100 for the app version of that script, I tried the free trial and that thing didn't even work either