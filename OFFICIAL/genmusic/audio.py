import subprocess
import numpy as np
print(np.version.version)
from collections.abc import Iterable
import sys
sys.path.append('genmusic/music-geometry-eval/music_geometry_eval')
import note_seq
import music_geometry_eval
import openai
import music21
import streamlit as st
import shutil

def generate_audio(band_name, song_name, i):
    
    openai.api_key = st.secrets["OPENAI_API_KEY"]
    SAMPLE_RATE = 16000
    CMM_mean = 2.2715
    CMM_std = 0.4831
    LM_mean = 2.0305
    LM_std = 0.5386
    CENT_mean = 0.3042
    CENT_std = 0.0891

    CMM_mean = 2.2715
    CMM_std = 0.4831

    LM_mean = 2.0305
    LM_std = 0.5386

    CENT_mean = 0.3042
    CENT_std = 0.0891
    SAMPLE_RATE = 16000
    sys.path.append('music-geometry-eval/music_geometry_eval')

    prompt = "X: 1 $ T: " + song_name + " $ C: " + band_name + " $ <song>"
    
    songs_with_scores = []
    score_arr = np.empty((0), np.float32)

    print("\n  Generating Song", i)
    response = openai.Completion.create(
        model="curie:ft-personal-2022-05-19-00-24-04",
        prompt=prompt,
        stop = " $ <end>",
        temperature=0.75,
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=0.0,
        max_tokens = 1000)

    # print(response)
    # print()

    formatted_prompt = "X: 1 $ T: " + song_name + " $ C: " + band_name + " $ L: 1/4 $ M: 4/4 $ K: C $ V: 1 treble"
    formatted_prompt = formatted_prompt.replace(" $ ", "\n")
    formatted_prompt = formatted_prompt.replace("<song>", "").strip()

    formatted_song = response["choices"][0]["text"].strip()
    formatted_song = formatted_song.replace('`', '"')
    formatted_song = formatted_song.replace(" $ ", "\n")
    new_song = formatted_prompt+ "\n" + formatted_song
    # print(new_song)
    with open(f"bg_audio_{i}.abc", "w") as new_song_file:
        new_song_file.write(new_song)

    song = music21.converter.parse(new_song)

    part = song.parts[0]
    chord_end = song.highestTime
    for pi in reversed(range(len(part))):
        p = part[pi]
    for ni in reversed(range(len(p))):
        n = p[ni]
        if type(n) == music21.harmony.ChordSymbol:
            chord_start = p.offset + n.offset
            n.duration.quarterLength = chord_end - chord_start
            n.volume = music21.volume.Volume(velocity=48)
            chord_end = chord_start
        elif type(n) == music21.note.Note:
            n.volume = music21.volume.Volume(velocity=64)
    file_name = f"bg_audio_{i}.mid"
    song.write('midi', fp=file_name)

    bashCommand = f"timidity bg_audio_{i}.mid -Ow -o bg_audio_{i}.wav"
    process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
    output, error = process.communicate()

    return f"bg_audio_{i}.wav"
