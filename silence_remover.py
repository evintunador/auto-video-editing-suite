import sys                                                                            
from moviepy.editor import VideoFileClip, concatenate_videoclips                      
from pydub import AudioSegment                                                        
from pydub.silence import detect_nonsilent                                            
import os            
from config import *                                                        
                                                                                         
def remove_silence(input_file, output_file, silence_thresh=silence_threshold, buff_time=500):     
    # Load the video file                                                             
    video = VideoFileClip(input_file)                                                 
                                                                                         
    # Extract the audio                                                               
    audio = video.audio                                                               
                                                                                         
    # Save the audio to a temporary file                                              
    audio_file = 'temp_audio.wav'                                                     
    audio.write_audiofile(audio_file)                                                 
                                                                                         
    # Load the audio with pydub                                                       
    audio_pydub = AudioSegment.from_wav(audio_file)                                   
                                                                                         
    # Delete the temporary file                                                       
    os.remove(audio_file)                                                             
                                                                                         
    # Detect non-silent segments                                                      
    nonsilent_segments = detect_nonsilent(audio_pydub, min_silence_len=minimum_silence_length, silence_thresh=silence_thresh)                                                        
                                                                                         
    # Add buffer time around the non-silent segments                                  
    nonsilent_segments_buffered = [[max(0, start - buff_time), min(len(audio_pydub), end + buff_time)] for start, end in nonsilent_segments]       
                                                                                         
    # Cut the video based on the buffered non-silent segments                         
    video_clips = [video.subclip(start / 1000, end / 1000) for start, end in nonsilent_segments_buffered]                                                          
    video_final = concatenate_videoclips(video_clips)                                 
                                                                                         
    # Save the final video to a file                                                  
    video_final.write_videofile(output_file, codec='libx264')                         
                                                                                         
if __name__ == '__main__':                                                            
    input_file = sys.argv[1]                                                          
    output_file = sys.argv[2]                                                         
    silence_thresh = int(sys.argv[3]) if len(sys.argv) > 3 else silence_threshold                   
    buff_time = int(sys.argv[4]) if len(sys.argv) > 4 else buffer_time                      
    remove_silence(input_file, output_file, silence_thresh, buff_time)  
