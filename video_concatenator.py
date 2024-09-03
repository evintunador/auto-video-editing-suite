import os
import subprocess
from pathlib import Path
import tempfile
import argparse

def check_ffmpeg():
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except FileNotFoundError:
        return False

def validate_input_files(file_paths):
    valid_files = []
    for file_path in file_paths:
        path = Path(file_path)
        if not path.exists():
            print(f"Error: File not found: {file_path}")
        elif not path.is_file():
            print(f"Error: Not a file: {file_path}")
        elif path.suffix.lower() != '.mp4':
            print(f"Error: Not an MP4 file: {file_path}")
        else:
            valid_files.append(str(path.resolve()))
    return valid_files

def get_video_duration(file_path):
    result = subprocess.run([
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        file_path
    ], capture_output=True, text=True, check=True)
    
    return float(result.stdout)

def process_timestamps(input_files, timestamp_files):
    merged_timestamps = []
    current_offset = 0.0

    for i, timestamp_file in enumerate(timestamp_files):
        video_duration = get_video_duration(input_files[i])
        video_name = os.path.basename(input_files[i])
        
        if timestamp_file == "[No Timestamp File]":
            hours = int(current_offset // 3600)
            minutes = int((current_offset % 3600) // 60)
            seconds = int(current_offset % 60)
            new_timestamp = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            merged_timestamps.append(f"{new_timestamp} {video_name}")
            current_offset += video_duration
        else:
            with open(timestamp_file, 'r') as f:
                lines = f.readlines()
            
            for line in lines:
                parts = line.strip().split(' ', 1)
                if len(parts) < 2:
                    continue
                timestamp, description = parts
                try:
                    hours, minutes, seconds = map(int, timestamp.split(':'))
                except ValueError:
                    continue
                total_seconds = hours * 3600 + minutes * 60 + seconds + current_offset
                hours = int(total_seconds // 3600)
                minutes = int((total_seconds % 3600) // 60)
                seconds = int(total_seconds % 60)
                new_timestamp = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                merged_timestamps.append(f"{new_timestamp} {description}")

            current_offset += video_duration

    return merged_timestamps

def write_merged_timestamps(merged_timestamps, output_timestamp_file):
    with open(output_timestamp_file, 'w') as f:
        for timestamp in merged_timestamps:
            f.write(f"{timestamp}\n")

def concatenate_videos(input_files, output_file):
    with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.txt') as temp_file:
        for file in input_files:
            temp_file.write(f"file '{file}'\n")
        temp_file_name = temp_file.name

    try:
        cmd = [
            "ffmpeg",
            "-f", "concat",
            "-safe", "0",
            "-i", temp_file_name,
            "-c", "copy",
            "-movflags", "+faststart",
            output_file
        ]
        
        print(f"Running FFmpeg command: {' '.join(cmd)}")
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"Concatenation complete. Output saved to {output_file}")
    except subprocess.CalledProcessError as e:
        print(f"Error during concatenation: {e}\nFFmpeg output: {e.stderr.decode()}")
    finally:
        os.unlink(temp_file_name)

    if not os.path.exists(output_file) or os.path.getsize(output_file) == 0:
        print(f"Failed to create output file or output file is empty: {output_file}")

def main(input_files, timestamp_files, output_file, output_timestamp_file):
    if not check_ffmpeg():
        print("FFmpeg is not installed or not in the system PATH.")
        return

    valid_files = validate_input_files(input_files)
    if not valid_files:
        print("No valid input files found.")
        return

    if timestamp_files:
        # Replace None values with "[No Timestamp File]"
        timestamp_files = ["[No Timestamp File]" if t is None else t for t in timestamp_files]
        merged_timestamps = process_timestamps(valid_files, timestamp_files)
        write_merged_timestamps(merged_timestamps, output_timestamp_file)
    else:
        print("No timestamp files provided. Skipping timestamp processing.")

    concatenate_videos(valid_files, output_file)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Concatenate videos and merge timestamps.")
    parser.add_argument('-iv', '--input-videos', nargs='+', required=True, help="Input video files (.mp4).")
    parser.add_argument('-it', '--input-timestamps', nargs='+', help="Input timestamp files (.txt). Use 'None' for missing files.")
    parser.add_argument('-ov', '--output-videos', required=True, help="Output video file (.mp4)")
    parser.add_argument('-ot', '--output-timestamps', help="Output timestamp file (.txt)")

    args = parser.parse_args()

    # Convert "None" strings to None objects
    timestamp_files = [None if t == "None" else t for t in args.timestamps] if args.timestamps else None

    main(args.input, timestamp_files, args.output, args.output_timestamps)