from moviepy.editor import *
from pydub import AudioSegment
from .text_to_speech import text_to_speech
import os
import sys
import warnings
warnings.filterwarnings("ignore")

def integrate_story(video_dir, audio_dir, paragraphs_dict, project_name):
    
    for paragraph_num in range(1, len(paragraphs_dict)+1):
        
        # add text
        video_file = video_dir + f"video_{paragraph_num}.mp4"
        text = paragraphs_dict[paragraph_num]
        video_withtext = add_text(paragraph_num, video_file, text)
        video_withtext = video_withtext.subclip(0, video_withtext.duration - 2)
        
        # generate text to speech
        text_to_speech(text, paragraph_num)
    
        # add audio
        duration = AudioFileClip(audio_dir + f"voice_audio_{paragraph_num}.mp3").duration + 9
        print("duration: ", duration)
        print("speed up: ", video_withtext.duration / duration)
        video_withtext = video_withtext.fx( vfx.speedx, video_withtext.duration / duration)
        video_withtextandaudio = add_audio(video_withtext, audio_dir + f"bg_audio_{paragraph_num}.wav", audio_dir + f"voice_audio_{paragraph_num}.mp3")
        # video_withtextandaudio = video_withtextandaudio.subclip(0, duration)
        video_withtextandaudio.write_videofile(f"integrate/data/final/final_{paragraph_num}.mp4")
        
    # integrate all clips
    integrate_videos("integrate/data/final/", project_name)

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
    
    voice_audioclip = AudioFileClip(voice_audio_file).set_start(3)
    bg_audioclip = AudioFileClip(bg_audio_file).subclip(0, voice_audioclip.duration + 10)
    print("voice_audioclip.duration: ", voice_audioclip.duration)
    print("bg_audioclip.duration: ", bg_audioclip.duration)

    new_audioclip = CompositeAudioClip([bg_audioclip, voice_audioclip])
    videoclip.audio = new_audioclip
    
    return videoclip
    # videoclip.write_videofile("final.mp4")
    
def integrate_videos(final_dir, project_name):
    # print(os.listdir(video_dir))
    # print(os.listdir(final_dir))
    sorted_clipnames = sorted([int(name.replace("final_", "").replace(".mp4", "")) for name in os.listdir(final_dir) if name.endswith(".mp4")])
    clips = [VideoFileClip(final_dir + f"final_{clip}" + ".mp4") for clip in sorted_clipnames]

    fade_duration = 5
    fade_clips = [clips[0]]
    print(len(clips))
    end = clips[0].end
    for i in range(1,len(clips)):
        print(f"Adding {i}th video...")
        print("END: ", end)
        fade_clips.append(clips[i].set_start(end-fade_duration).crossfadein(fade_duration))
        end += clips[i-1].duration
        
    # fade_clips = clips[0] + [clip.crossfadein(fade_duration).set_start(clips[i].end-1).crossfadein(1) for clip in clips[1:]] 
    final_clip = CompositeVideoClip(fade_clips)
    final_clip.write_videofile(f"integrate/data/{project_name}_final.mp4")
    
# video_dir = "data/video_clips/"
# audio_dir = "data/audio_clips/"
# paragraphs_dict = {1: "This is the first paragraph", 2: "This is the second paragraph"}
    
# integrate_story(video_dir, audio_dir, paragraphs_dict)