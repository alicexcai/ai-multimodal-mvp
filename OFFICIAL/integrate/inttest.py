from moviepy.editor import *
from pydub import AudioSegment
from text_to_speech import text_to_speech
import os
import sys

def integrate_story(video_dir, audio_dir, paragraphs_dict):
    
    for paragraph_num in range(1, len(paragraphs_dict)+1):
        
        # add text
        video_file = video_dir + f"video_{paragraph_num}.mp4"
        text = paragraphs_dict[paragraph_num]
        video_withtext = add_text(paragraph_num, video_file, text)
        
        # generate text to speech
        text_to_speech(text, paragraph_num)
    
        # add audio
        video_withtextandaudio = add_audio(video_withtext, audio_dir + f"bg_audio_{paragraph_num}.wav", audio_dir + f"voice_audio_{paragraph_num}.mp3")
        video_withtextandaudio.write_videofile(f"data/final/final_{paragraph_num}.mp4")
        
    # integrate all clips
    integrate_videos("data/final/")

def add_text(paragraph_num, video_file, text):

    clip = VideoFileClip(video_file) 
        
    # # clipping of the video  
    # # getting video for only starting 10 seconds 
    # clip = clip.subclip(0, 10) 
    # # Reduce the audio volume (volume x 0.8) 
    # clip = clip.volumex(0.8) 
        
    # Generate a text clip 
    # txt_clip = TextClip(text, fontsize = 12, color = 'white', stroke_color='black') 
    # txt_clip = txt_clip.set_pos('center').set_duration(10) 
    screensize = (clip.size[0],100)
    txt_clip = (TextClip(text, color='white',
        font="Keep-Calm-Medium", kerning=0, interline=0, size = 
        screensize, method='caption', align='center', bg_color='black')
        .set_position(('center', 'bottom'))
        .set_duration(clip.duration)
        # .set_start(1)
        )

    
    video = CompositeVideoClip([clip, txt_clip]) 
    
    return video

def add_audio(videoclip, bg_audio_file, voice_audio_file):
    
    # videoclip = VideoFileClip(video_file)
    bg_audioclip = AudioFileClip(bg_audio_file)
    voice_audioclip = AudioFileClip(voice_audio_file)

    new_audioclip = CompositeAudioClip([bg_audioclip, voice_audioclip])
    videoclip.audio = new_audioclip
    
    return videoclip
    # videoclip.write_videofile("final.mp4")
    
def integrate_videos(final_dir):
    # print(os.listdir(video_dir))
    # print(os.listdir(final_dir))
    sorted_clipnames = sorted([int(name.replace("final_", "").replace(".mp4", "")) for name in os.listdir(final_dir)])
    clips = [VideoFileClip(clip) for clip in sorted_clipnames]
    # final_clip = CompositeVideoClip(clips)
    fade_duration = 5
    fade_clips = [clip.crossfadein(fade_duration) for clip in clips]
    final_clip = concatenate_videoclips(fade_clips, padding = -fade_duration)
    final_clip.write_videofile("data/final.mp4")
    
# video_dir = "data/video_clips/"
# audio_dir = "data/audio_clips/"
# paragraphs_dict = {1: "This is the first paragraph", 2: "This is the second paragraph"}
    
# integrate_story(video_dir, audio_dir, paragraphs_dict)

textvideo = add_text(1, '/Users/alicecai/Desktop/ai-multimodal/OFFICIAL/integrate/data/video_clips/video_1.mp4', 'This is a test. This is a story. This story continues on for a long time. This is a test. This is a story. This story continues on for a long time.')
textvideo.write_videofile(f"data/final/test.mp4")