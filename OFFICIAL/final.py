from gettext import bind_textdomain_codeset
import streamlit as st
import pandas as pd
import pygsheets
from datetime import datetime
import openai
import requests
from collections import defaultdict
from genmusic import audio
from integrate import integration
import boto3
import os

# APP SETUP

apptitle = 'THE IMAGINATION MACHINE'
st.set_page_config(page_title=apptitle, page_icon=":brain:")
st.title("THE IMAGINATION MACHINE")

openai.api_key = st.secrets["OPENAI_API_KEY"]

# DECLARE PARAMS

class Params:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        
params = Params()
params.paragraph = defaultdict()
txt_params = Params()
img_params = Params()
img_params.cap_params = defaultdict()
audio_params = Params()
audio_params.info_params = defaultdict()

base_path = "https://ai-multimodal.s3.us-east-2.amazonaws.com"

### DELETE ###
# results = Params()
# results.generated_text = defaultdict()
# img_results = Params()
# img_results.output_bucket = defaultdict()
# music_results = Params()
# music_results.generated_music = defaultdict()

# get data from location
# data_df.loc[(data_df['project'] == selected_project) & (data_df['paragraph_num'] == 1)]['gen_text']

# Data from columns


    
# SELECT PROJECT

gc = pygsheets.authorize(service_file='.streamlit/ai-art-farm-2c65230a4396.json')
sheet = gc.open('AIMultimodalMVP_Database')
projects_wks = sheet.worksheet('title', 'projects')
projects_records = projects_wks.get_all_records()
projects_list = [project['project_alias'] for project in projects_records]

selected_project = st.sidebar.selectbox("Select your story", projects_list, index=1)  

def get_data(datacol, project):
    data_wks = sheet.worksheet('title', 'main')
    data_records = data_wks.get_all_records()
    data_dict = {data['paragraph_num'] : data[datacol] for data in data_records if data['project'] == project}
    return data_dict

def store_data(datacol, project, paragraph_num, value):
    data_wks = sheet.worksheet('title', 'main')
    data_records = data_wks.get_all_records()
    data_df = pd.DataFrame.from_dict(data_records)
    cell = data_df.index[(data_df['project'] == project) & (data_df['paragraph_num'] == paragraph_num)].tolist()[0]+2
    data_wks.update_value(datacol + str(cell),value)
    
def store_paragraph(paragraph, paragraph_num):
    try: 
        store_data('C', selected_project, paragraph_num, paragraph)
    except:
        data_wks = sheet.worksheet('title', 'main')
        data_records = data_wks.get_all_records()
        cell = len(data_records)+2
        # new_paragraph_data = [selected_project, paragraph_num, paragraph]
        # data_wks.insert_rows(last_row_data, number=1, values=new_paragraph_data)
        # st.write('A' + str(cell) + ':C' + str(cell))
        # st.write([selected_project, str(paragraph_num), paragraph])
        data_wks.update_values('A' + str(cell) + ':C' + str(cell), [[selected_project, str(paragraph_num), paragraph]])
    

with st.sidebar.expander("Create new story"):
    new_project_name = st.text_input("Enter new story name")
    click_create_new_project = st.button("Save story")
    
if click_create_new_project:
    last_row_project = len(projects_list)+1
    # DO NOT EDIT UNDERLYING DB, ONLY VIEWS - if projects get deleted, id will sometimes skip a value
    new_project_data = [last_row_project, new_project_name, None, datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")]
    projects_wks.insert_rows(last_row_project, number=1, values=new_project_data)

num_boxes = st.sidebar.slider("Number of paragraphs", 0, 50, 3)

with st.sidebar.expander("Generative Text Parameters"):
    txt_params.model = 'davinci'
    txt_params.max_tokens = st.slider("Max Tokens", min_value=10, max_value=500, value=100)
    txt_params.stop = '###'
    txt_params.top_p = 1.0
    txt_params.temperature = st.slider("Temperature", min_value=0.0, max_value=1.0, value=0.7)
    txt_params.frequency_penalty = st.slider("Frequency Penalty", min_value=0.0, max_value=1.0, value=0.0)
    txt_params.presence_penalty = st.slider("Presence Penalty", min_value=0.0, max_value=1.0, value=0.0)
    txt_params.best_of = st.slider("Best of", min_value=1, max_value=10, value=1)

with st.sidebar.expander("Generative Illustration Parameters"):
    img_params.img_size = st.slider("Image Size", 50, 1000, 400)
    img_params.clip_guidance_scale = st.slider("CLIP Guidance", 10000, 100000, 50000)
    img_params.tv_scale = st.slider("TV Scale", 10000, 100000, 80000)
    img_params.num_steps = st.slider("Number of Steps", 1, 1000, 300)
    
def generate_text(paragraph, paragraph_num):
    txt_params.prompt = paragraph
    text_response = openai.Completion.create(
        model=txt_params.model,
        prompt=txt_params.prompt,
        temperature=txt_params.temperature,
        max_tokens=txt_params.max_tokens,
        top_p=txt_params.top_p,
        frequency_penalty=txt_params.frequency_penalty,
        presence_penalty=txt_params.presence_penalty,
        stop=txt_params.stop,
        )
    text = text_response['choices'][0]['text']   
    
    # non hard-coded system?
    store_data(datacol='K', project=selected_project, paragraph_num=paragraph_num, value=text)
    store_data(datacol='F', project=selected_project, paragraph_num=paragraph_num, value=str(txt_params.__dict__))


def generate_illustrations(paragraph, paragraph_num):
    
    img_params.cap_params['model'] = 'davinci'
    img_params.cap_params['temperature'] = 0.7
    img_params.cap_params['max_tokens'] = 100
    # img_params.cap_params['top_p'] = 1.0
    # img_params.cap_params['frequency_penalty'] = 0.0
    # img_params.cap_params['presence_penalty'] = 0.0
    img_params.cap_params['stop'] = '###'
    
    def generate_caption(scene):
        img_params.cap_params['prompt'] = f"""Write a caption for the scene: Cyberspace. A consensual hallucination experienced daily by billions of legitimate operators, in every nation, by children being taught mathematical concepts. A graphic representation of data abstracted from the banks of every computer in the human system. Unthinkable complexity. Lines of light ranged in the nonspace of the mind, clusters and constellations of data. Like city lights, receding.
            Caption: cyberspace consensual hallucination | graphic representation of data abstracted from computers | lines of light ranged in the nonspace of the mind | clusters and constellations of data

            ###

            Write a caption for the scene: She rides on a flying train through snowy slums in uncertainty and danger.
            Caption: high speed train driving through snowy slums, past shabby houses and ramshackle streets and abandoned factory buildings | action photo with motion blur of train | landscape of mobile homes stacked on top of each other | birds eye view of city industrial district in a state of complete disrepair

            ###

            Write a caption for the scene: A year here and he still dreamed of cyberspace, hope fading nightly. All the speed he took, all the turns he'd taken and the corners he cut in Night City, and he'd still see the matrix in his dreams, bright lattices of logic unfolding across that colourless void.
            Caption: bright lattices of logic unfolding across that colourless void | intricate recursion  portal of digital virtual matrix realm to the internet data traffic realm

            ###

            Write a caption for the scene: Her soul was a dandelion, carried to all corners of the earth by the wind, scattering into the clouds beyond. Sometimes, when she’s out here alone, she can feel the pulse of something bigger, as if all things animate were beating in unison, a glory and a connection that sweeps her out of herself, out of her consciousness, so that nothing has a name, not in Latin, not in English, not in any known language. All around her, in the sunlight, snow melts, crystals evaporate into a steam, into nothing. In the firelight, fragile things burst and disappear.
            Caption: dandelion soul carried to all corners of the earth by the wind | fractal composition with a central sunflower | geometric mandala of swirling color, snow melting | crystals evaporating into a steam, into nothing

            ###

            Write a caption for the scene: The alien walked out from the chamber and extended its three-fingered hand to me. Hesitantly, I shook its hand.
            Caption: alien walking out from chamber, extending its three-fingered hand | alien from planet of the apes | the humanoid figure extends the three-fingered hand of the hand to the human figure

            ###

            Write a caption for the scene: {scene}
            Caption:"""
        
        caption_response = openai.Completion.create(
                model=img_params.cap_params['model'],
                prompt=img_params.cap_params['prompt'],
                temperature=img_params.cap_params['temperature'],
                max_tokens=img_params.cap_params['max_tokens'],
                # top_p=img_params.cap_params['top_p'],
                # frequency_penalty=img_params.cap_params['frequency_penalty'],
                # presence_penalty=img_params.cap_params['presence_penalty'],
                stop=img_params.cap_params['stop'],
                )
            
        caption = caption_response['choices'][0]['text'].strip() + " | ArtStation; CGSociety"
        return caption

    # send request with caption
    
    img_params.caption = generate_caption(paragraph)
    project_bucket = selected_project.replace(" ", "_")
    store_data(datacol='D', project=selected_project, paragraph_num=paragraph_num, value=img_params.caption)
    gen_img = f"{base_path}/admin/{project_bucket}/{paragraph_num}"
    store_data(datacol='G', project=selected_project, paragraph_num=paragraph_num, value=str(img_params.__dict__))
    store_data(datacol='I', project=selected_project, paragraph_num=paragraph_num, value=gen_img)
    
    url = 'https://ai-multimodal.loca.lt/getImage'
    request_data = {
        'caption': img_params.caption.strip(),
        'user': "admin",
        'project': project_bucket,
        'paragraph_num': paragraph_num,
        'clip_guidance_scale': img_params.clip_guidance_scale,
        'tv_scale': img_params.tv_scale,
        'img_size': img_params.img_size,
        'num_steps': img_params.num_steps,            
        }
    x = requests.post(url, data = request_data)

def generate_music(paragraph, paragraph_num):
    
    audio_params.info_params['model'] = 'davinci'
    audio_params.info_params['temperature'] = 0.7
    audio_params.info_params['max_tokens'] = 100
    # img_params.cap_params['top_p'] = 1.0
    # img_params.cap_params['frequency_penalty'] = 0.0
    # img_params.cap_params['presence_penalty'] = 0.0
    audio_params.info_params['stop'] = '###'
    
    def generate_songinfo(scene):
        audio_params.info_params['prompt'] = f"""Write a song name for the scene: Cyberspace. A consensual hallucination experienced daily by billions of legitimate operators, in every nation, by children being taught mathematical concepts. A graphic representation of data abstracted from the banks of every computer in the human system. Unthinkable complexity. Lines of light ranged in the nonspace of the mind, clusters and constellations of data. Like city lights, receding.
            Song name: Cyberpunk Hallucinations | Matrix Brothers

            ###

            Write a song name for the scene: She rides on a flying train through snowy slums in uncertainty and danger.
            Song name: Flying into the Great Unknown | Snow Wolves

            ###

            Write a song name for the scene: A year here and he still dreamed of cyberspace, hope fading nightly. All the speed he took, all the turns he'd taken and the corners he cut in Night City, and he'd still see the matrix in his dreams, bright lattices of logic unfolding across that colourless void.
            Song name: High on Cyberspace | Cyberpunk Outlaws

            ###

            Write a song name for the scene: Her soul was a dandelion, carried to all corners of the earth by the wind, scattering into the clouds beyond. Sometimes, when she’s out here alone, she can feel the pulse of something bigger, as if all things animate were beating in unison, a glory and a connection that sweeps her out of herself, out of her consciousness, so that nothing has a name, not in Latin, not in English, not in any known language. All around her, in the sunlight, snow melts, crystals evaporate into a steam, into nothing. In the firelight, fragile things burst and disappear.
            Song name: Ethereal Piano Music | Beethoven

            ###

            Write a song name for the scene: The alien walked out from the chamber and extended its three-fingered hand to me. Hesitantly, I shook its hand.
            Song name: Alien Spacejam | Sci-Fi Tunes

            ###

            Write a song name for the scene: {scene}
            Song name:"""
        
        info_response = openai.Completion.create(
                model=audio_params.info_params['model'],
                prompt=audio_params.info_params['prompt'],
                temperature=audio_params.info_params['temperature'],
                max_tokens=audio_params.info_params['max_tokens'],
                # top_p=img_params.cap_params['top_p'],
                # frequency_penalty=img_params.cap_params['frequency_penalty'],
                # presence_penalty=img_params.cap_params['presence_penalty'],
                stop=audio_params.info_params['stop'],
                )
            
        band_name = info_response['choices'][0]['text'].split(' | ')[0].strip()
        song_name = info_response['choices'][0]['text'].split(' | ')[1].strip()
        return band_name, song_name
    
    audio_params.band_name, audio_params.song_name = generate_songinfo(paragraph)
    
    audio_path = audio.generate_audio(audio_params.band_name, audio_params.song_name, paragraph_num)
    
    ### aws
    # def savetoS3Bucket(audio_path):
    project_bucket = selected_project.replace(" ", "_")
    upload_path = f"admin/{project_bucket}/{paragraph_num}/{audio_path}"
    session = boto3.Session(
        aws_access_key_id=st.secrets["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=st.secrets["AWS_SECRET_ACCESS_KEY"],
    )
    s3 = session.resource('s3')
    s3.meta.client.upload_file(Filename=f'{audio_path}', Bucket='ai-multimodal', Key=upload_path)
    
    store_data(datacol='E', project=selected_project, paragraph_num=paragraph_num, value=str(audio_params.band_name + " by " + audio_params.song_name))
    gen_audio = f"{base_path}/admin/{project_bucket}/{paragraph_num}/{audio_path}"
    store_data(datacol='H', project=selected_project, paragraph_num=paragraph_num, value=str(audio_params.__dict__))
    store_data(datacol='J', project=selected_project, paragraph_num=paragraph_num, value=gen_audio)
    os.remove(audio_path)
    os.remove(audio_path.replace(".wav", ".abc"))
    os.remove(audio_path.replace(".wav", ".mid"))

for paragraph_num in range(1, num_boxes + 1):
    try:
        paragraph_text = get_data('text', selected_project)[paragraph_num]
    except:
        paragraph_text = ""
    
    inputcol, savecol = st.columns([9,1])
    params.paragraph[paragraph_num] = inputcol.text_area("Paragraph %s" %paragraph_num, paragraph_text, key=paragraph_num)
    savecol.markdown("---")
    if savecol.button("Save", key=paragraph_num):
        store_paragraph(paragraph=params.paragraph[paragraph_num], paragraph_num=paragraph_num)
    
    # if st.button("Save paragraph"):
    #     store_data(datacol='C', project=selected_project, paragraph_num=paragraph_num, value=params.paragraph[paragraph_num])
        
    tcol, tcolf = st.columns([1, 8])
    icol, icolf = st.columns([1, 6])
    mcol, mcolf = st.columns([1, 6])
    if tcol.button("Write", key=paragraph_num):
        generate_text(params.paragraph[paragraph_num], paragraph_num)
    
    if icol.button("Illustrate", key=paragraph_num):
        generate_illustrations(params.paragraph[paragraph_num], paragraph_num)
        
    if mcol.button("Compose", key=paragraph_num):
        generate_music(params.paragraph[paragraph_num], paragraph_num)
    
    
    
    # DISPLAY RESUlTS
    
    gentext_dict = get_data('gen_text', selected_project)
    with tcolf.expander("Generated Text"):
        if paragraph_num in gentext_dict.keys() and gentext_dict[paragraph_num] != "":
            st.write(gentext_dict[paragraph_num])
        else:
            st.code("No text generated.")
            
    genimg_dict = get_data('gen_img', selected_project)
    imgprompt_dict = get_data('img_prompt', selected_project)
    with icolf.expander("Generated Illustration"):
        if paragraph_num in genimg_dict.keys() and genimg_dict[paragraph_num] != "":
            # imgl, img1, img2, img3 = st.columns(4)
            # st.write(genimg_dict[paragraph_num] + "/latest.png")
            st.write("Caption: ", imgprompt_dict[paragraph_num])
            st.image(genimg_dict[paragraph_num] + "/latest.png", width=400)
            # img1.image(genimg_dict[paragraph_num] + f"/progress_10.png")
            # img2.image(genimg_dict[paragraph_num] + f"/progress_50.png")
            # img3.image(genimg_dict[paragraph_num] + f"/progress_135.png")
        else:
            st.code("No illustration generated.")
            
    genaudio_dict = get_data('gen_audio', selected_project)
    audioprompt_dict = get_data('audio_prompt', selected_project)
    with mcolf.expander("Generated Audio"):
        # st.audio("https://ai-multimodal.s3.us-east-2.amazonaws.com/song01.wav")
        if paragraph_num in genaudio_dict.keys() and genaudio_dict[paragraph_num] != "":
            st.write("Song name: ", audioprompt_dict[paragraph_num])
            st.audio(genaudio_dict[paragraph_num])
        else:
            st.code("No audio generated.")
            
    st.markdown("---")
        
        
    # with icolf.expander("Generated Illustration"):
    #     if i in img_results.output_bucket.keys():
    #         imgv, img1, img2, img3 = st.columns(4)
    #         iteration = 1
    #         # while iteration < 135:
    #         #     try:
    #         #         imgv.image(img_results.output_bucket[i] + f"/progress_{iteration}.png")
    #         #         iteration = iteration + 1
    #         #     except:
    #         #         iteration = iteration - 1
                
    #         img1.image(output_bucket[i] + f"/progress_10.png")
    #         img2.image(output_bucket[i] + f"/progress_50.png")
    #         img3.image(output_bucket[i] + f"/progress_135.png")
    #     else:
    #         st.code("No illustration generated.")
        
    # with mcolf.expander("Generated Music"):
    #     if i in music_results.generated_music.keys():
    #         st.audio(music_results.generated_music[i])
    #     else:
    #         st.code("No music generated.")
        
        
### INSTRUCTIONS

def download_project_data(project):
    project_bucket = project.replace(" ", "_")
    paragraphs_dict = get_data('text', project)
    num_paragraphs = len(paragraphs_dict)
    
    def download_data(data_path, destination_path):
        response = requests.get(data_path)
        open(destination_path, "wb").write(response.content)
            
    for paragraph_num in range(1, num_paragraphs+1):
        download_data(f"https://ai-multimodal.s3.us-east-2.amazonaws.com/admin/{project_bucket}/{paragraph_num}/video_{paragraph_num}.mp4", f"integrate/data/video_clips/video_{paragraph_num}.mp4")
        download_data(f"https://ai-multimodal.s3.us-east-2.amazonaws.com/admin/{project_bucket}/{paragraph_num}/bg_audio_{paragraph_num}.wav", f"integrate/data/audio_clips/bg_audio_{paragraph_num}.wav")
    
    # command = "ffmpeg -i 1.mp4 -i 2.mp4 -filter_complex \"xfade=offset=4.5:duration=1\" output.mp4"
def begin_integration(project):
    project_bucket = project.replace(" ", "_")
    paragraphs_dict = get_data('text', project)
    # num_paragraphs = len(paragraphs_dict)
    integration.integrate_story('integrate/data/video_clips/', 'integrate/data/audio_clips/', paragraphs_dict, project_bucket)
    

st.sidebar.markdown("---")
# with st.sidebar.expander("Export Project"):
if st.sidebar.button("Download Story"):
    with st.spinner("Downloading story..."):
        download_project_data(selected_project)
        st.success("Story downloaded.")
        
if st.sidebar.button("Integrate Story"):
    with st.spinner("Integrating story..."):
        begin_integration(selected_project)
        st.success("Story integrated.")
        # st.button("Download integrated story")
    # if st.button("Save Story"):
    #     with st.spinner("Integrating story..."):
    #         integrate_story(selected_project)
    #         st.success("Story integrated.")
    #         st.button("Download integrated story")

st.sidebar.markdown("---")
with st.sidebar.expander("Instructions"):
    st.markdown("""
                ### Instructions:
                * Begin writing your story in an input box. 
                * When you're ready to generate an illustration, click the GENERATE button.
                * Each input box generates one illustration and one song. You can separate your story by paragraphs or however you like.
                * Use the slider on the sidebar to add new input boxes.
                ---
                """)