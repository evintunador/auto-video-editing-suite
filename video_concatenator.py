import subprocess
import os
import argparse

def concatenate_videos(input_files, output):
    # Check if input files exist
    for file in input_files:
        if not os.path.exists(file):
            raise FileNotFoundError(f"Input file does not exist: {file}")

    # Create a temporary file list
    with open("temp_file_list.txt", "w") as f:
        for file in input_files:
            f.write(f"file '{file}'\n")

    # FFmpeg command to concatenate videos
    command = [
        "ffmpeg",
        "-f", "concat",
        "-safe", "0",
        "-i", "temp_file_list.txt",
        "-c", "copy",
        output
    ]

    # Execute the FFmpeg command
    try:
        subprocess.run(command, check=True)
        print(f"Videos concatenated successfully. Output saved as {output}")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while concatenating videos: {e}")
    finally:
        # Clean up the temporary file
        os.remove("temp_file_list.txt")

def main():
    parser = argparse.ArgumentParser(description="Concatenate multiple MP4 files.")
    parser.add_argument("input_files", nargs="+", help="Input MP4 files to concatenate")
    parser.add_argument("-o", "--output", default="output.mp4", help="Output file name (default: output.mp4)")
    
    args = parser.parse_args()
    
    concatenate_videos(args.input_files, args.output)

if __name__ == "__main__":
    main()