from pynput import keyboard
import time
import os
import argparse

hotkey = '='
start_time = None
timestamps = []
timestamps_file = "timestamps.txt"

def parse_arguments():
    parser = argparse.ArgumentParser(description="Timestamp recorder")
    parser.add_argument("-k", "--hotkey", default="=", help="Hotkey to record timestamp (default: '=')")
    parser.add_argument("-f", "--filename", default="timestamps.txt", help="Output file name (default: timestamps.txt)")
    parser.add_argument("-e", "--endkey", default="esc", help="Key to end recording (default: 'esc')")
    return parser.parse_args()

def on_activate():
    global start_time
    
    if start_time is None:
        start_time = time.time()
        timestamps.append("0:00 Timer started!")
        print("0:00 Timer started!")
        return

    elapsed_time = time.time() - start_time
    minutes, seconds = divmod(int(elapsed_time), 60)
    
    timestamp = f"{minutes}:{seconds:02d} timestamp"
    timestamps.append(timestamp)
    print(timestamp)  # Print the new timestamp

current_keys = set()

def on_press(key):
    if key == keyboard.KeyCode.from_char(hotkey):
        on_activate()
    elif key == end_key:
        return False  # Stop listener

def on_release(key):
    try:
        current_keys.remove(key)
    except KeyError:
        pass

def main():
    global hotkey, timestamps_file, end_key
    args = parse_arguments()
    hotkey = args.hotkey
    timestamps_file = args.filename

    if args.endkey == 'esc':
        end_key = keyboard.Key.esc
    else:
        end_key = keyboard.KeyCode.from_char(args.endkey)

    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()

    with open(timestamps_file, "w") as f:
        f.write("\n".join(timestamps))

if __name__ == "__main__":
    main()