import os
import sys
import subprocess
from pathlib import Path

def check_ffmpeg():
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except FileNotFoundError:
        print("Error: FFmpeg is not installed or not in the system PATH.")
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

def check_output_file(output_path):
    path = Path(output_path)
    if path.exists():
        response = input(f"Output file {output_path} already exists. Overwrite? (y/n): ")
        if response.lower() != 'y':
            print("Operation cancelled.")
            return False
    return True

def get_video_info(file_path):
    try:
        result = subprocess.run([
            "ffprobe",
            "-v", "error",
            "-select_streams", "v:0",
            "-count_packets",
            "-show_entries", "stream=width,height,r_frame_rate,codec_name",
            "-of", "csv=p=0",
            file_path
        ], capture_output=True, text=True, check=True)
        
        output = result.stdout.strip().split(',')
        
        if len(output) != 4:
            print(f"Unexpected ffprobe output format: {output}")
            return None

        # Create a dictionary with all values
        info = {
            'codec': output[0],
            'width': output[1],
            'height': output[2],
            'frame_rate': output[3]
        }

        # Convert width and height to integers
        info['width'] = int(info['width'])
        info['height'] = int(info['height'])

        # Convert frame rate to float
        numerator, denominator = map(int, info['frame_rate'].split('/'))
        info['frame_rate'] = numerator / denominator

        return info
    except subprocess.CalledProcessError as e:
        print(f"Error running ffprobe: {e}")
        return None
    except ValueError as e:
        print(f"Error parsing ffprobe output: {e}")
        print(f"ffprobe output: {result.stdout}")
        return None

def concatenate_videos(input_files, output_file):
    first_video_info = get_video_info(input_files[0])
    if not first_video_info:
        print("Failed to get video info for the first file. Aborting.")
        return

    filter_complex = []
    inputs = []
    
    for i, file in enumerate(input_files):
        inputs.extend(['-i', file])
        filter_complex.append(f'[{i}:v]scale={first_video_info["width"]}:{first_video_info["height"]}:force_original_aspect_ratio=decrease,pad={first_video_info["width"]}:{first_video_info["height"]}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps={first_video_info["frame_rate"]}[v{i}];')
        filter_complex.append(f'[{i}:a]aformat=sample_rates=44100:channel_layouts=stereo[a{i}];')

    for i in range(len(input_files)):
        filter_complex.append(f'[v{i}][a{i}]')
    
    filter_complex.append(f'concat=n={len(input_files)}:v=1:a=1[outv][outa]')
    
    try:
        cmd = [
            "ffmpeg",
            *inputs,
            '-filter_complex', ''.join(filter_complex),
            '-map', '[outv]',
            '-map', '[outa]',
            '-c:v', first_video_info['codec'],
            '-c:a', 'aac',
            output_file
        ]
        print(f"Running FFmpeg command: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)
        print(f"Concatenation complete. Output saved to {output_file}")
    except subprocess.CalledProcessError as e:
        print(f"Error during concatenation: {e}")

def main():
    if len(sys.argv) < 3:
        print("Usage: python script.py input1.mp4 input2.mp4 ... output.mp4")
        return

    if not check_ffmpeg():
        return

    input_files = sys.argv[1:-1]
    output_file = sys.argv[-1]

    valid_files = validate_input_files(input_files)
    if not valid_files:
        print("No valid input files found. Exiting.")
        return

    if not check_output_file(output_file):
        return

    concatenate_videos(valid_files, output_file)

if __name__ == "__main__":
    main()