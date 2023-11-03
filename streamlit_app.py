import streamlit as st
import openai, boto3, json
from elevenlabs import set_api_key
from elevenlabs import generate, play, save

openai.api_key = st.secrets['OPENAI_API_KEY']
set_api_key(st.secrets['ELEVENLABS_KEY'])
chapters = [
  "0_Premonition",
  "1_Domination",
  "2_Conversation",
  "3_Presentation",
  "4_Session",
  "5_Connection",
  "6_Exploration",
  "7_Rationalization",
  "8_Union",
  "9_Revelation",
  "10_Manipulation",
]

@st.cache_data  
def get_text(chapters):
# get the .txt files from each chapter in the list chapters, 
# under the following structure chapter_name/script/chapter_name.txt 
# from the s3 bucket called biomachines

    # create an S3 client
    s3 = boto3.client('s3')

    # set the name of the S3 bucket
    bucket_name = 'biomachines'

    # create a list to store the text from each file
    text_list = []

    # loop through each chapter in the list
    for chapter in chapters:
        # set the path to the file
        file_path = f"{chapter}/script/{chapter}.txt"
        
        # get the object from S3
        obj = s3.get_object(Bucket=bucket_name, Key=file_path)
        
        # read the contents of the file
        text = obj['Body'].read().decode('utf-8')
        
        # append the text to the list
        text_list.append(text)
        
    # print the list of text
    return "".join(text_list)


def finale(text):
    # Generate a story finale from the ChatGPT model
    inst = '''Generate a story finale under 1000 characters based on the previous text:''' 
    completion = openai.ChatCompletion.create(
        model='gpt-3.5-turbo-16k',
        messages= [
            {'role': 'system', 'content': inst },
            {'role': 'user', 'content': text }]
    )
    return completion.choices[0].message.content

def jsonify(text):
    # Generate a response from the ChatGPT model
    inst = '''Turn the following text into a json list, with keys being speaker and content. 
    the speaker key that can take the values Eva, Alec or Narrator''' 
    completion = openai.ChatCompletion.create(
        model='gpt-3.5-turbo-16k',
        messages= [
            {'role': 'system', 'content': inst },
            {'role': 'user', 'content': text }]
    )
    return completion.choices[0].message.content

def load_json(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        data = json.load(file)
    return data

def display_data(data):
    for entry in data:
        speaker = entry["speaker"]
        content = entry["content"]
        
        # Print the speaker and content
        if speaker == "narrator":
            st.write(content)
        else:
            st.write(f"{speaker}: {content}")

def generate_audio(jasonl, voices):
    all_audios = []
    n = 0

    for entry in jasonl:
        speaker = entry["speaker"]
        content = entry["content"]
        voice = voices.get(speaker, voices["Narrator"])  # Default to 'Narrator' if voice not found

        # Generate audio for the content
        audio = generate(
            text=content,
            voice=voice,
            model="eleven_monolingual_v1"
        )
        all_audios.append(audio)
        save(audio,f'audio/{n}_{speaker}.mp3')
        n += 1

    # Concatenate all audio segments (assuming the library returns audio in a format that can be concatenated)
    final_audio = b"".join(all_audios)

    # Save the concatenated audio to the output file
    save(final_audio,'audio.mp3')

    return all_audios

def main():
    st.set_page_config(page_title="Finale", page_icon=":guardsman:", layout="wide")
    st.title("Finale 🎬")

    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Introduction", "Generate Finale", "Generate Audio", "Display Dialogues", "Play Audio"])

    if page == "Introduction":
        st.header("Introduction")
        st.write("This app generates a story finale under 1000 characters based on the previous text. It also turns the generated text into a json list, with keys being speaker and content. The speaker key can take the values Eva, Alec or Narrator. Finally, it generates audio for the content and displays the dialogues.")

    elif page == "Generate Finale":
        st.header("Generate Finale")
        input_text = get_text(chapters)
        text = st.text_area("Enter the previous text:", input_text, height=300)
        if st.button("Generate"):
            output = finale(text)
            st.write(output)
            with open('11_Finale.txt', 'w') as f:
                f.write(output)
            jasonl = jsonify(output)
            with open('11_Finale.json', 'w') as f:
                f.write(jasonl)
            st.download_button(
                label="Download JSON",
                data=jasonl,
                file_name='11_Finale.json',
                mime='application/json',
            )

    elif page == "Generate Audio":
        st.header("Generate Audio")
        filename = st.file_uploader("Upload JSON file", type=["json"])
        if filename is not None:
            jasonl = load_json(filename.name)
            voices = {
                'Alec':'Adam',
                'Eva':'Rachel',
                'Narrator': 'Antoni',
            }
            all_audios = generate_audio(jasonl, voices)
            for a in all_audios:
                st.audio(a)
            st.success("Audio generated successfully!")

    elif page == "Display Dialogues":
        st.header("Display Dialogues")
        filename = st.file_uploader("Upload JSON file", type=["json"])
        if filename is not None:
            jasonl = load_json(filename.name)
            display_data(jasonl)

    elif page == "Play Audio":
        st.header("Play Audio")
        # load audio from folder
        audio_file = open('audio.mp3', 'rb')
        audio_bytes = audio_file.read()
        st.audio(audio_bytes, format='audio/mp3')

if __name__ == "__main__":
    main()
