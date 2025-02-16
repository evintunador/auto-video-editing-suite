#!/usr/bin/env python
"""
video_cropper.py

This script crops a given video into multiple parts based on crop definitions provided via the command line.
Each crop definition should follow the format: name:x:y:width:height

Example usage:
    python video_cropper.py /path/to/video.mp4 --crop "left:0:0:608:1080" --crop "middle:656:0:608:1080" --crop "right:1312:0:608:1080"

Output files are saved in the same directory as the input video with names:
    {input_basename}_{crop_name}.mp4
"""

import argparse
import os
import sys
import subprocess

def parse_crop_option(crop_str):
    """
    Parses a crop option in the format name:x:y:width:height.
    
    Args:
        crop_str (str): Crop definition string.
        
    Returns:
        dict: A dictionary with keys: 'name', 'x', 'y', 'width', 'height'.
    
    Raises:
        ValueError: If the crop string is not in the correct format or numeric values fail conversion.
    """
    parts = crop_str.split(':')
    if len(parts) != 5:
        raise ValueError(f"Crop option '{crop_str}' is invalid. Expected format name:x:y:width:height")
    name = parts[0]
    try:
        x = int(parts[1])
        y = int(parts[2])
        width = int(parts[3])
        height = int(parts[4])
    except ValueError:
        raise ValueError(f"Crop option '{crop_str}' contains invalid numeric values.")
    return {"name": name, "x": x, "y": y, "width": width, "height": height}

def get_video_dimensions(input_file):
    """
    Uses ffprobe to extract the video width and height.
    
    Args:
        input_file (str): Path to the input video file.
        
    Returns:
        tuple: (width, height) of the video.
    """
    cmd = [
        "ffprobe",
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height",
        "-of", "csv=s=x:p=0",
        input_file
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        output = result.stdout.strip()
        if not output:
            raise ValueError("Could not determine video dimensions.")
        width, height = output.split("x")
        return int(width), int(height)
    except subprocess.CalledProcessError as e:
        print(f"Error retrieving video dimensions: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as ve:
        print(f"Error processing video dimensions: {ve}", file=sys.stderr)
        sys.exit(1)

def get_output_file(input_file, crop_name):
    """
    Constructs the output file path for a given crop.
    
    Args:
        input_file (str): Path to the input video file.
        crop_name (str): Custom name for the crop.
        
    Returns:
        str: Output file path.
    """
    directory, filename = os.path.split(input_file)
    base, _ = os.path.splitext(filename)
    output_filename = f"{base}_{crop_name}.mp4"
    return os.path.join(directory, output_filename)

def process_crop(input_file, crop):
    """
    Processes a single crop by invoking ffmpeg with the appropriate crop filter.
    
    Args:
        input_file (str): Path to the input video file.
        crop (dict): Crop definition containing 'x', 'y', 'width', 'height', and 'name'.
        
    Returns:
        bool: True if the crop was processed successfully, False otherwise.
    """
    output_file = get_output_file(input_file, crop["name"])
    crop_filter = f"crop={crop['width']}:{crop['height']}:{crop['x']}:{crop['y']}"
    cmd = [
        "ffmpeg",
        "-i", input_file,
        "-filter:v", crop_filter,
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-c:a", "copy",
        output_file,
        "-y"  # Overwrite if output exists
    ]
    print(f"Processing crop '{crop['name']}' with filter: {crop_filter}")
    try:
        subprocess.run(cmd, check=True)
        print(f"Crop '{crop['name']}' created successfully at: {output_file}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error processing crop '{crop['name']}': {e}", file=sys.stderr)
        return False

def main():
    parser = argparse.ArgumentParser(
        description="Crop a video into multiple parts based on specified crop definitions."
    )
    parser.add_argument("input_file", help="Path to the input video file")
    parser.add_argument("--crop", action="append", required=True, 
                        help="Crop definition in the format name:x:y:width:height. Example: left:0:0:608:1080")
    args = parser.parse_args()

    input_file = args.input_file
    if not os.path.isfile(input_file):
        print(f"Error: The input file '{input_file}' does not exist or is not a file.", file=sys.stderr)
        sys.exit(1)

    # Retrieve input video dimensions.
    video_width, video_height = get_video_dimensions(input_file)
    print(f"Input video dimensions: {video_width}x{video_height}")

    crops = []
    # Parse and validate each crop definition.
    for crop_str in args.crop:
        try:
            crop = parse_crop_option(crop_str)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
        
        # Check that crop offsets and sizes are within video bounds.
        if crop["x"] < 0 or crop["y"] < 0:
            print(f"Error: Crop '{crop['name']}' has negative x or y offset.", file=sys.stderr)
            sys.exit(1)
        if crop["width"] <= 0 or crop["height"] <= 0:
            print(f"Error: Crop '{crop['name']}' must have positive width and height.", file=sys.stderr)
            sys.exit(1)
        if crop["x"] + crop["width"] > video_width:
            print(f"Error: Crop '{crop['name']}' exceeds video width (x + width = {crop['x'] + crop['width']} > {video_width}).", file=sys.stderr)
            sys.exit(1)
        if crop["y"] + crop["height"] > video_height:
            print(f"Error: Crop '{crop['name']}' exceeds video height (y + height = {crop['y'] + crop['height']} > {video_height}).", file=sys.stderr)
            sys.exit(1)
        crops.append(crop)

    # Process each crop sequentially.
    all_success = True
    for crop in crops:
        if not process_crop(input_file, crop):
            all_success = False

    if not all_success:
        print("One or more crops failed.", file=sys.stderr)
        sys.exit(1)
    else:
        print("All crops processed successfully.")

if __name__ == "__main__":
    main()
