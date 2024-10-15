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
        
        if timestamp_file is None:
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
                    time_parts = timestamp.split(':')
                    if len(time_parts) == 2:  # MM:SS format
                        minutes, seconds = map(int, time_parts)
                        hours = 0
                    elif len(time_parts) == 3:  # HH:MM:SS format
                        hours, minutes, seconds = map(int, time_parts)
                    else:
                        print(f"Invalid timestamp format: {timestamp}")
                        continue
                    total_seconds = hours * 3600 + minutes * 60 + seconds + current_offset
                    hours = int(total_seconds // 3600)
                    minutes = int((total_seconds % 3600) // 60)
                    seconds = int(total_seconds % 60)
                    new_timestamp = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                    merged_timestamps.append(f"{new_timestamp} {description}")
                except ValueError:
                    print(f"Invalid timestamp: {timestamp}")
                    continue

            current_offset += video_duration

    return merged_timestamps

def write_merged_timestamps(merged_timestamps, output_timestamp_file):
    with open(output_timestamp_file, 'w') as f:
        for timestamp in merged_timestamps:
            f.write(f"{timestamp}\n")

def get_media_info(file_path):
    media_info = {}
    # Video info
    result = subprocess.run([
        "ffprobe",
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=codec_name,width,height,r_frame_rate",
        "-of", "default=noprint_wrappers=1:nokey=1",
        file_path
    ], capture_output=True, text=True)
    v_info = result.stdout.strip().split('\n')
    if len(v_info) >= 4:
        media_info['v_codec'] = v_info[0]
        media_info['width'] = v_info[1]
        media_info['height'] = v_info[2]
        media_info['frame_rate'] = v_info[3]
    else:
        media_info['v_codec'] = None

    # Audio info
    result = subprocess.run([
        "ffprobe",
        "-v", "error",
        "-select_streams", "a:0",
        "-show_entries", "stream=codec_name,sample_rate,channels",
        "-of", "default=noprint_wrappers=1:nokey=1",
        file_path
    ], capture_output=True, text=True)
    a_info = result.stdout.strip().split('\n')
    if len(a_info) >= 3:
        media_info['a_codec'] = a_info[0]
        media_info['sample_rate'] = a_info[1]
        media_info['channels'] = a_info[2]
    else:
        media_info['a_codec'] = None

    return media_info

def check_media_compatibility(valid_files):
    media_infos = []
    for file in valid_files:
        info = get_media_info(file)
        media_infos.append(info)

    # Now compare parameters
    first_info = media_infos[0]
    incompatible = False
    for i, info in enumerate(media_infos[1:], 1):
        if info['v_codec'] != first_info['v_codec']:
            print(f"Warning: Video codec of file {valid_files[i]} ({info['v_codec']}) does not match the first file ({first_info['v_codec']})")
            incompatible = True
        if info['width'] != first_info['width'] or info['height'] != first_info['height']:
            print(f"Warning: Resolution of file {valid_files[i]} ({info['width']}x{info['height']}) does not match the first file ({first_info['width']}x{first_info['height']})")
            incompatible = True
        if info['frame_rate'] != first_info['frame_rate']:
            print(f"Warning: Frame rate of file {valid_files[i]} ({info['frame_rate']}) does not match the first file ({first_info['frame_rate']})")
            incompatible = True
        if info['a_codec'] != first_info['a_codec']:
            print(f"Warning: Audio codec of file {valid_files[i]} ({info['a_codec']}) does not match the first file ({first_info['a_codec']})")
            incompatible = True
        if info['sample_rate'] != first_info['sample_rate']:
            print(f"Warning: Audio sample rate of file {valid_files[i]} ({info['sample_rate']}) does not match the first file ({first_info['sample_rate']})")
            incompatible = True
        if info['channels'] != first_info['channels']:
            print(f"Warning: Number of audio channels of file {valid_files[i]} ({info['channels']}) does not match the first file ({first_info['channels']})")
            incompatible = True

    return incompatible, media_infos

def concatenate_videos(input_files, output_file, incompatible):
    if not incompatible:
        # Use concat demuxer
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
    else:
        # Use concat filter with re-encoding
        inputs = []
        filter_complex = ''
        for idx, file in enumerate(input_files):
            inputs.extend(['-i', file])
            filter_complex += f'[{idx}:v:0][{idx}:a:0]'
        filter_complex += f'concat=n={len(input_files)}:v=1:a=1[outv][outa]'
        cmd = ['ffmpeg']
        cmd.extend(inputs)
        cmd.extend([
            '-filter_complex', filter_complex,
            '-map', '[outv]',
            '-map', '[outa]',
            '-movflags', '+faststart',
            output_file
        ])
        print(f"Running FFmpeg command: {' '.join(cmd)}")
        try:
            subprocess.run(cmd, check=True)
            print(f"Concatenation complete with re-encoding. Output saved to {output_file}")
        except subprocess.CalledProcessError as e:
            print(f"Error during concatenation: {e}\nFFmpeg output: {e.stderr.decode()}")

def main(input_files, timestamp_files, output_file, output_timestamp_file):
    if not check_ffmpeg():
        print("FFmpeg is not installed or not in the system PATH.")
        return

    valid_files = validate_input_files(input_files)
    if not valid_files:
        print("No valid input files found.")
        return

    incompatible, media_infos = check_media_compatibility(valid_files)

    if timestamp_files:
        merged_timestamps = process_timestamps(valid_files, timestamp_files)
        write_merged_timestamps(merged_timestamps, output_timestamp_file)
    else:
        print("No timestamp files provided. Skipping timestamp processing.")

    concatenate_videos(valid_files, output_file, incompatible)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Concatenate videos and merge timestamps.")
    parser.add_argument('-iv', '--input-videos', nargs='+', required=True, help="Input video files (.mp4).")
    parser.add_argument('-it', '--input-timestamps', nargs='+', help="Input timestamp files (.txt). Use 'None' for missing files.")
    parser.add_argument('-ov', '--output-videos', required=True, help="Output video file (.mp4)")
    parser.add_argument('-ot', '--output-timestamps', help="Output timestamp file (.txt)")

    args = parser.parse_args()

    # Convert "None" strings to None objects
    timestamp_files = [None if t == "None" else t for t in args.input_timestamps] if args.input_timestamps else None

    main(args.input_videos, timestamp_files, args.output_videos, args.output_timestamps)