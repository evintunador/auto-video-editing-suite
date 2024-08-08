import argparse
import os
import subprocess
from tqdm import tqdm
import shutil
import ffmpeg
from datetime import timedelta

def process_video(input_file, output_file, chunk_duration, db_threshold, buffer_duration, timestamps_file=None, output_timestamps_file=None):
    temp_dir = "temp_chunks"
    os.makedirs(temp_dir, exist_ok=True)
    
    min_silence_length = buffer_duration * 4
    
    try:
        # Split video into chunks
        chunk_list = split_video(input_file, chunk_duration, temp_dir)
        
        processed_chunks = []
        silence_intervals = []
        total_silence_duration = 0
        cumulative_silence_removal = []
        
        for i, chunk in enumerate(tqdm(chunk_list, desc="Processing chunks")):
            silence_parts, chunk_duration = detect_silence(chunk, db_threshold, buffer_duration, min_silence_length)
            output_chunk = f"{temp_dir}/processed_chunk_{i}.mp4"
            chunk_silence_duration = cut_silence(chunk, silence_parts, chunk_duration, output_chunk)
            
            # Record silence intervals with their original start times
            chunk_start_time = i * chunk_duration
            for start, end in silence_parts:
                silence_intervals.append((chunk_start_time + start, chunk_start_time + end))
            
            total_silence_duration += chunk_silence_duration
            cumulative_silence_removal.append(total_silence_duration)
            processed_chunks.append(output_chunk)
        
        # Check for inconsistencies in silence intervals
        check_silence_intervals(silence_intervals, buffer_duration)
        
        # Debug check: compare cumulative silence removal with total from intervals
        debug_check_silence_removal(silence_intervals, cumulative_silence_removal)
        
        # Concatenate processed chunks
        concatenate_chunks(processed_chunks, output_file)
        
        # Process timestamps if provided
        if timestamps_file:
            if not output_timestamps_file:
                base, ext = os.path.splitext(timestamps_file)
                output_timestamps_file = f"{base}_adjusted{ext}"
            process_timestamps(timestamps_file, output_timestamps_file, silence_intervals)
        
        # Log information about the process
        print(f"\nTotal silence removed: {timedelta(seconds=total_silence_duration)}")
        if timestamps_file:
            print(f"Adjusted timestamps saved to: {output_timestamps_file}")
        
    finally:
        # Clean up temporary files
        for file in os.listdir(temp_dir):
            os.remove(os.path.join(temp_dir, file))
        os.rmdir(temp_dir)

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
        return 0

    # Generate a list of parts to keep
    keep_parts = []
    if silence_parts[0][0] > 0:
        keep_parts.append([0, silence_parts[0][0]])
    
    for i in range(len(silence_parts) - 1):
        keep_parts.append([silence_parts[i][1], silence_parts[i+1][0]])
    
    # Check if there's non-silent content after the last silence part
    if silence_parts[-1][1] < chunk_duration:
        keep_parts.append([silence_parts[-1][1], chunk_duration])

    # Calculate total silence duration
    silence_duration = sum(end - start for start, end in silence_parts)

    # If there are no parts to keep, it means the entire chunk is silent
    if not keep_parts:
        # Create a short (e.g., 0.1 second) silent video
        cmd = f"ffmpeg -f lavfi -i anullsrc=channel_layout=stereo:sample_rate=44100 -f lavfi -i color=c=black:s=1280x720:r=30 -t 0.1 -c:a aac -c:v libx264 {output_chunk}"
        subprocess.run(cmd, shell=True, check=True)
        return silence_duration

    # Generate filter complex string
    filter_complex = ""
    for i, (start, end) in enumerate(keep_parts):
        filter_complex += f"[0:v]trim=start={start}:end={end},setpts=PTS-STARTPTS[v{i}];"
        filter_complex += f"[0:a]atrim=start={start}:end={end},asetpts=PTS-STARTPTS[a{i}];"
    
    filter_complex += "".join(f"[v{i}][a{i}]" for i in range(len(keep_parts)))
    filter_complex += f"concat=n={len(keep_parts)}:v=1:a=1[outv][outa]"
    
    cmd = f"ffmpeg -i {input_chunk} -filter_complex '{filter_complex}' -map '[outv]' -map '[outa]' {output_chunk}"
    subprocess.run(cmd, shell=True, check=True)

    return silence_duration

def concatenate_chunks(chunk_list, output_file):
    print('Beginning final trimmed chunk concatenation')
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

def process_timestamps(input_file, output_file, silence_intervals):
    adjusted_timestamps = []
    timestamps_adjusted = 0

    try:
        with open(input_file, 'r') as f:
            lines = f.readlines()

        for line in lines:
            parts = line.strip().split(' ', 1)
            if len(parts) != 2:
                raise ValueError(f"Invalid timestamp format in line: {line}")

            time_str, description = parts
            time_parts = time_str.split(':')
            if len(time_parts) not in (2, 3):
                raise ValueError(f"Invalid time format in line: {line}")

            if len(time_parts) == 2:
                minutes, seconds = map(float, time_parts)
                hours = 0
            else:
                hours, minutes, seconds = map(float, time_parts)

            original_seconds = hours * 3600 + minutes * 60 + seconds
            
            # Calculate silence removed up to this timestamp
            silence_removed = sum(min(end, original_seconds) - start 
                                  for start, end in silence_intervals 
                                  if start < original_seconds)
            
            adjusted_seconds = max(0, original_seconds - silence_removed)
            
            adjusted_time = timedelta(seconds=adjusted_seconds)
            adjusted_time_str = f"{int(adjusted_time.total_seconds() // 3600):02d}:{int((adjusted_time.total_seconds() % 3600) // 60):02d}:{adjusted_time.total_seconds() % 60:06.3f}"
            adjusted_time_str = adjusted_time_str[:-4]
            if adjusted_time.total_seconds() < 3600:
                adjusted_time_str = adjusted_time_str[3:]  # Remove leading zeros for times less than an hour
            
            adjusted_timestamps.append(f"{adjusted_time_str} {description}")
            timestamps_adjusted += 1

        with open(output_file, 'w') as f:
            for timestamp in adjusted_timestamps:
                f.write(f"{timestamp}\n")

        print(f"Adjusted {timestamps_adjusted} timestamps")

    except Exception as e:
        print(f"Error processing timestamps: {e}")
        raise

def check_silence_intervals(silence_intervals, buffer_duration):
    for i, (start, end) in enumerate(silence_intervals):
        if end - start < buffer_duration:  # Check for very short intervals (less than 10ms)
            print(f"Warning: Very short silence interval detected: {start:.3f} - {end:.3f}")
        if i > 0 and start < silence_intervals[i-1][1]:
            print(f"Warning: Overlapping silence intervals detected: {silence_intervals[i-1]} and {(start, end)}")

def debug_check_silence_removal(silence_intervals, cumulative_silence_removal):
    total_from_intervals = sum(end - start for start, end in silence_intervals)
    total_from_cumulative = cumulative_silence_removal[-1] if cumulative_silence_removal else 0
    
    if abs(total_from_intervals - total_from_cumulative) > 0.001:  # Allow for small floating-point discrepancies
        print(f"Warning: Discrepancy in total silence removal")
        print(f"Total from intervals: {total_from_intervals:.3f}")
        print(f"Total from cumulative: {total_from_cumulative:.3f}")
        print(f"Difference: {abs(total_from_intervals - total_from_cumulative):.3f}")

def main():
    parser = argparse.ArgumentParser(description="Remove silence from video files and adjust timestamps.")
    parser.add_argument("input_file", help="Path to the input video file")
    parser.add_argument("-o", "--output_file", help="Path to the output video file")
    parser.add_argument("-d", "--db_threshold", type=float, default=-45, help="Decibel threshold for silence detection. Default -45, raise to remove louder portions")
    parser.add_argument("-b", "--buffer_duration", type=float, default=0.2, help="Buffer duration around non-silent parts. Default 0.1 seconds")
    parser.add_argument("-c", "--chunk_duration", type=int, default=150, help="Duration of video chunks to work with. Default 150 seconds")
    parser.add_argument("-m", "--min_silence_factor", type=float, default=0.6, help="Minimum silence duration required in order for it to be cut out. Default 0.4 seconds, must be greater than or equal to buffer duration")
    parser.add_argument("-t", "--timestamps", help="Path to the input timestamps file")
    parser.add_argument("--output_timestamps", help="Path to the output adjusted timestamps file")
    
    args = parser.parse_args()
    
    if not args.output_file:
        base, ext = os.path.splitext(args.input_file)
        args.output_file = f"{base}_no_silence{ext}"
    
    process_video(args.input_file, args.output_file, args.chunk_duration, args.db_threshold, args.buffer_duration, args.timestamps, args.output_timestamps)

if __name__ == "__main__":
    main()