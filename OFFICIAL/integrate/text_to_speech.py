def text_to_speech(text, paragraph_num):
    
    print("Executing text to speech...")
    print(text, paragraph_num)
    
    import os
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="/Users/alicecai/Desktop/ai-multimodal/OFFICIAL/.streamlit/ai-art-farm-2c65230a4396.json"
    from google.cloud import texttospeech

    client = texttospeech.TextToSpeechClient()

    synthesis_input = texttospeech.SynthesisInput(text=text)
    
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US", ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )

    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )

    with open(f"integrate/data/audio_clips/voice_audio_{paragraph_num}.mp3", "wb") as out:
        out.write(response.audio_content)
        print(f'Audio content written to file "integrate/data/audio_clips/voice_audio_{paragraph_num}.mp3"')
        