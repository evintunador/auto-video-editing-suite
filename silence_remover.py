import sys                                                                                                                      
import os            
from config import *    
from tqdm import tqdm
import logging
import argparse
import shutil

# supposed to suppress all of moviepy's annoying output but i don't think it works
# does moviepy use print statements? maybe that's why 
if not debug_mode:
    logging.getLogger('moviepy').setLevel(logging.CRITICAL)

from moviepy.editor import VideoFileClip, concatenate_videoclips                      
from pydub import AudioSegment                                                        
from pydub.silence import detect_nonsilent  

                                                                                         
def remove_silence(input_file, output_file, silence_thresh=silence_threshold, buff_time=buffer_time, debug_mode=debug_mode):    
    # reset temp clips folder
    try:
        shutil.rmtree('temp_clips')  
        os.makedirs('temp_clips/')
    except FileNotFoundError:
        os.makedirs('temp_clips/')

    # Load the video file                                                             
    video = VideoFileClip(input_file)                                                 
                                                                                         
    # Extract the audio                                                               
    audio = video.audio                                                               
                                                                                         
    # Save the audio to a temporary file                                              
    audio_file = 'temp_audio.wav'   
    try:
        os.remove(audio_file) # jic there's one there from the previous run   
    except FileNotFoundError:
        pass                                               
    audio.write_audiofile(audio_file)                                                 
                                                                                         
    # Load the audio with pydub                                                       
    audio_pydub = AudioSegment.from_wav(audio_file)                                   
                                                                                         
    # Delete the temporary file                                                       
    if not debug_mode:
        os.remove(audio_file)                                                             
                                                                                         
    # Detect non-silent segments                                                      
    nonsilent_segments = detect_nonsilent(audio_pydub, min_silence_len=minimum_silence_length, silence_thresh=silence_thresh)                                                        
                                                                                         
    # Add buffer time around the non-silent segments                                  
    nonsilent_segments_buffered = [[max(0, start - buff_time), min(len(audio_pydub), end + buff_time)] for start, end in nonsilent_segments]       

    if debug_mode:
        # initialize a list to hold silent segments
        silent_segments = []

        # Add segments between nonsilent segments
        for i in tqdm(range(len(nonsilent_segments) - 1), desc="Finding Silent Segments"):
            silent_start = nonsilent_segments[i][1]
            silent_end = nonsilent_segments[i + 1][0]
            silent_segments.append((silent_start, silent_end))

        # Add segment from end of last nonsilent segment to end of audio
        if nonsilent_segments[-1][1] < len(audio_pydub):
            silent_segments.append((nonsilent_segments[-1][1], len(audio_pydub)))

        # Remove buffer time around the silent segments                                  
        silent_segments_buffered = [[max(0, start + buff_time), min(len(audio_pydub), end - buff_time)] for start, end in silent_segments]

        # clear silent clips from previous run
        try:
            shutil.rmtree('temp_silent_clips')  
            os.makedirs('temp_silent_clips/')
        except FileNotFoundError:
            os.makedirs('temp_silent_clips/')

        # Cut the video based on the buffered non-silent segments and save them to temp_folder
        clip_paths = []
        for i, (start, end) in tqdm(enumerate(silent_segments_buffered), desc="Writing Silent Clips"):
            clip = video.subclip(start / 1000, end / 1000)
            clip.write_videofile(f"temp_silent_clips/clip_{i}.mov", codec='libx264')   
            clip_paths.append(f"temp_silent_clips/clip_{i}.mov")  

        # clean up memory
        del silent_segments, silent_segments_buffered, clip_paths, clip, i, start, end

    # Cut the video based on the buffered non-silent segments and save them to temp_folder
    clip_paths = []
    for i, (start, end) in tqdm(enumerate(nonsilent_segments_buffered), desc="Writing Nonsilent Clips"):
        clip = video.subclip(start / 1000, end / 1000)
        clip.write_videofile(f"temp_clips/clip_{i}.mov", codec='libx264')   
        clip_paths.append(f"temp_clips/clip_{i}.mov")  

    # clean up memory
    del video, audio, audio_file, audio_pydub, nonsilent_segments, nonsilent_segments_buffered

    # Initialize final clip
    concatenated = VideoFileClip(clip_paths[0])
    #concatenated.write_videofile('temp_clips/concatenated.mov', codec='libx264')

    # Iterative concatenation
    for i in tqdm(range(1, len(clip_paths)), desc="Concatenating Clips"):
        clip = VideoFileClip(clip_paths[i])
        concatenated = concatenate_videoclips([concatenated, clip])
        del clip  # Remove clip from memory                                                                      

    # Write the final concatenated clip
    concatenated.write_videofile(output_file, codec='libx264')

    # Clean up: remove temporary clips and folder
    if not debug_mode:
        shutil.rmtree('temp_clips')     
        shutil.rmtree('temp_silent_clips')        
                                                                                         
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Remove silence from video files.')

    parser.add_argument('input_file', type=str, help='Path to the input file.')
    parser.add_argument('-o', '--output_file', type=str, default='output.mov', help='Path to the output file.')
    parser.add_argument('-s', '--silence_thresh', type=int, default=silence_threshold, help='Silence threshold in dB.')
    parser.add_argument('-b', '--buff_time', type=int, default=buffer_time, help='Buffer time in milliseconds.')
    parser.add_argument('-d', '--debug', action='store_true', default=debug_mode, help='Enable debug mode. Keeps all temporary files and creates files for the silence gaps.')

    args = parser.parse_args()

    remove_silence(args.input_file, args.output_file, args.silence_thresh, args.buff_time, args.debug)
