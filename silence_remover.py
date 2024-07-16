import argparse
import os
import subprocess
from tqdm import tqdm
import shutil

def process_video(input_file, output_file, chunk_duration=300, db_threshold=-30, buffer_duration=0.25):
    temp_dir = "temp_chunks"
    os.makedirs(temp_dir, exist_ok=True)
    
    min_silence_length = buffer_duration * 4
    
    try:
        # Split video into chunks
        chunk_list = split_video(input_file, chunk_duration, temp_dir)
        
        processed_chunks = []
        for i, chunk in enumerate(tqdm(chunk_list, desc="Processing chunks")):
            silence_parts, chunk_duration = detect_silence(chunk, db_threshold, buffer_duration, min_silence_length)
            output_chunk = f"{temp_dir}/processed_chunk_{i}.mp4"
            cut_silence(chunk, silence_parts, chunk_duration, output_chunk)
            processed_chunks.append(output_chunk)
        
        # Concatenate processed chunks
        concatenate_chunks(processed_chunks, output_file)
        
    finally:
        # Clean up temporary files
        #for file in os.listdir(temp_dir):
            #os.remove(os.path.join(temp_dir, file))
        #os.rmdir(temp_dir)
        print("skipping cleanup")

def split_video(input_file, chunk_duration, temp_dir):
    cmd = f"ffmpeg -i {input_file} -c copy -f segment -segment_time {chunk_duration} -reset_timestamps 1 {temp_dir}/chunk_%03d.mp4"
    subprocess.run(cmd, shell=True, check=True)
    return sorted([os.path.join(temp_dir, f) for f in os.listdir(temp_dir) if f.startswith("chunk_")])

def detect_silence(input_chunk, db_threshold, buffer_duration, min_silence_length):
    cmd = f"ffmpeg -i {input_chunk} -af silencedetect=noise={db_threshold}dB:d={min_silence_length} -f null -"
    try:
        output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode()
    except subprocess.CalledProcessError as e:
        print(f"Error running FFmpeg command: {e}")
        return []

    silence_parts = []
    for line in output.split('\n'):
        try:
            if "silence_start" in line:
                start = float(line.split("silence_start: ")[1])
                silence_parts.append([max(0, start + buffer_duration), None])
            elif "silence_end" in line:
                end = float(line.split("silence_end: ")[1].split()[0])
                silence_duration = float(line.split("silence_duration: ")[1])
                if silence_duration >= min_silence_length:
                    silence_parts[-1][1] = end - buffer_duration
                else:
                    silence_parts.pop()  # Remove the last silence part if it's too short
        except (IndexError, ValueError) as e:
            print(f"Error parsing FFmpeg output line: {line}")
            print(f"Error details: {e}")
            continue

    # Get the duration of the chunk
    duration = float(subprocess.check_output(f"ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 {input_chunk}", shell=True).decode().strip())

    return silence_parts, duration

def cut_silence(input_chunk, silence_parts, chunk_duration, output_chunk):
    if not silence_parts:
        shutil.copy(input_chunk, output_chunk)
        return

    # Generate a list of parts to keep
    keep_parts = []
    if silence_parts[0][0] > 0:
        keep_parts.append([0, silence_parts[0][0]])
    
    for i in range(len(silence_parts) - 1):
        keep_parts.append([silence_parts[i][1], silence_parts[i+1][0]])
    
    # Check if there's non-silent content after the last silence part
    if silence_parts[-1][1] < chunk_duration:
        keep_parts.append([silence_parts[-1][1], chunk_duration])

    # If there are no parts to keep, it means the entire chunk is silent
    if not keep_parts:
        # Create a short (e.g., 0.1 second) silent video
        cmd = f"ffmpeg -f lavfi -i anullsrc=channel_layout=stereo:sample_rate=44100 -f lavfi -i color=c=black:s=1280x720:r=30 -t 0.1 -c:a aac -c:v libx264 {output_chunk}"
        subprocess.run(cmd, shell=True, check=True)
        return

    # Generate filter complex string
    filter_complex = ""
    for i, (start, end) in enumerate(keep_parts):
        filter_complex += f"[0:v]trim=start={start}:end={end},setpts=PTS-STARTPTS[v{i}];"
        filter_complex += f"[0:a]atrim=start={start}:end={end},asetpts=PTS-STARTPTS[a{i}];"
    
    filter_complex += "".join(f"[v{i}][a{i}]" for i in range(len(keep_parts)))
    filter_complex += f"concat=n={len(keep_parts)}:v=1:a=1[outv][outa]"
    
    cmd = f"ffmpeg -i {input_chunk} -filter_complex '{filter_complex}' -map '[outv]' -map '[outa]' {output_chunk}"
    subprocess.run(cmd, shell=True, check=True)

def concatenate_chunks(chunk_list, output_file):
    input_args = []
    for chunk in chunk_list:
        input_args.extend(['-i', chunk])
    
    filter_complex = ''.join(f'[{i}:v][{i}:a]' for i in range(len(chunk_list))) + \
                     f'concat=n={len(chunk_list)}:v=1:a=1[outv][outa]'
    
    cmd = ['ffmpeg'] + input_args + [
        '-filter_complex', filter_complex,
        '-map', '[outv]', '-map', '[outa]',
        '-c:v', 'libx264', '-c:a', 'aac',
        output_file
    ]
    
    try:
        subprocess.run(cmd, check=True, stderr=subprocess.PIPE, universal_newlines=True)
    except subprocess.CalledProcessError as e:
        print(f"Error during concatenation: {e}")
        print(f"FFmpeg error output: {e.stderr}")
        raise

def main():
    parser = argparse.ArgumentParser(description="Remove silence from video files.")
    parser.add_argument("input_file", help="Path to the input video file")
    parser.add_argument("-o", "--output_file", help="Path to the output video file")
    parser.add_argument("-d", "--db_threshold", type=float, default=-45, help="Decibel threshold for silence detection. Default -45, raise to remove louder portions")
    parser.add_argument("-b", "--buffer_duration", type=float, default=0.1, help="Buffer duration around non-silent parts. Default 0.1 seconds")
    parser.add_argument("-c", "--chunk_duration", type=int, default=150, help="Duration of video chunks to work with (rather than using up hella ram by doing the entire video at once). Default 150 seconds")
    parser.add_argument("-m", "--min_silence_factor", type=float, default=0.4, help="Minimum silence duration required in order for it to be cut out. Default 0.4 seconds, must be greater than or equal to buffer duration")
    
    args = parser.parse_args()
    
    if not args.output_file:
        base, ext = os.path.splitext(args.input_file)
        args.output_file = f"{base}_no_silence{ext}"
    
    process_video(args.input_file, args.output_file, args.chunk_duration, args.db_threshold, args.buffer_duration)

if __name__ == "__main__":
    main()