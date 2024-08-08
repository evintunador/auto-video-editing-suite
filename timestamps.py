from pynput import keyboard
import time
import os

hotkey = '`'
start_time = None
timestamps = []
timestamps_file = "timestamps.txt"

def on_activate():
    global start_time
    
    if start_time is None:
        start_time = time.time()
        print("Timer started!")
        timestamps.append("0:00 Intro")
        print("0:00 Intro")  # Print the Intro timestamp
        return

    elapsed_time = time.time() - start_time
    minutes, seconds = divmod(int(elapsed_time), 60)
    
    timestamp = f"{minutes}:{seconds:02d}"
    timestamps.append(timestamp)
    print(timestamp)  # Print the new timestamp

current_keys = set()

def on_press(key):
    if key == keyboard.KeyCode.from_char(hotkey):
        on_activate()
    elif key == keyboard.Key.esc:
        return False  # Stop listener

def on_release(key):
    try:
        current_keys.remove(key)
    except KeyError:
        pass

with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
    listener.join()

with open(timestamps_file, "w") as f:
    f.write("\n".join(timestamps))