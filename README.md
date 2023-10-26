# video-silence-remover

This repo takes a .mov video from quicktime and removes silent portions as a quick and easy way to edit awkward silences out of videos

## Repo Contents

- `silence-remover.py` - does everything. Call it 
- `config.py` - this will let you edit the settings

## SETUP

1. Clone the repository to your local machine.
2. Install the required Python packages by running `pip install -r requirements.txt` in your terminal.
3. Optionally edit values in `config.py` to suit your needs. The default values work pretty well for both my inbuilt laptop mic and my $50 amazon microphone
    - `minimum_silence_length` defaults to one second (1000 milliseconds). Maybe you only want to cut out significantly longer gaps idk
    - `silence_threshold` is measured in decibels. Set to a lower value if it's cutting out too much, higher value if it's not cutting out enough. Yes it is supposed to be negative
    - `buffer_time` implements some silent gaps surrounging the useful sound so the final file it doesn't come out jittery. Not sure why you'd change this one
    - `debug_mode` Set to `True` if you want to keep all temporary files as well as the silent portions. Might be helpful for debugging; if you feel like too much or too little is being cut out you could take a look at these temporary files, edit the other settings, and then run again to see if that fixes your issue. Or maybe you might want those files for your video editing process
        - *BUG: When `debug_mode=False` all the `moviepy` print lines are supposed to be suppressed but for some reason they show up anyways. Might fix eventually bc it annoys me*

## USAGE

1. Run `python silence_remover.py "path/to/video/file/input.mov"`
    - Optionally run with arguments to edit settings without having to permanently change `config.py` like so:
    `python silence_remover.py "path/to/video/file/input.mov" -o "desired/path/to/video/file/output.mov" -s -38 -b 250 --debug`
2. Be annoyed by the excessive output of moviepy
3. Enjoy your shittily edited video 

 ## NOTES

 I've only really tested this on `.mov` files (from Apple's quicktime app) but at one point awhile ago I used it on an `.mp4` and it worked fine. 

 I use it for my youtube channel https://www.youtube.com/channel/UCeQhm8DwHBg_YEYY0KGM1GQ go check it out

 I originally had the idea and when I searched for it online I found https://github.com/carykh/jumpcutter but their version was hella glitchy for me so I just wrote it from scratch. Also wtf is with them charging $100 for the app version of that script, I tried the free trial and that thing didn't work either