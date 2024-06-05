import streamlit as st
import openai
from pydub import AudioSegment
import re
import tempfile
import os

# Function to generate speech
def generate_speech(text, voice="onyx", model="tts-1"):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as speech_file:
        response = client.audio.speech.create(
            model=model,
            voice=voice,
            input=text
        )
        response.stream_to_file(speech_file.name)
        return AudioSegment.from_mp3(speech_file.name)

# Function to generate silence
def generate_silence(duration):
    return AudioSegment.silent(duration=int(duration * 1000))

# Function to split meditation script
def split_meditation_script(script):
    pattern = r'(\n+|\[pause \d+\])'
    parts = re.split(pattern, script)
    return [part for part in parts if part]

# Function to process script
def process_script(script):
    parts = split_meditation_script(script)
    combined = AudioSegment.empty()

    for part in parts:
        if '[pause' in part:
            seconds = int(re.findall(r'\d+', part)[0])
            combined += generate_silence(seconds)
        elif part.strip() == '':
            combined += generate_silence(0.9)
        else:
            combined += generate_speech(part.strip())

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as final_file:
        combined.export(final_file.name, format="mp3")
        return final_file.name

# Streamlit UI
st.title("Guided Meditation Script Generator")

api_key = st.text_input("Enter OpenAI API Key", type="password")
prompt = st.text_area("Enter your prompt")

if st.button("Generate Audio"):
    if api_key and prompt:
        openai.api_key = api_key
        client = openai

        completion = client.chat.completions.create(
          model="gpt-3.5-turbo",
          messages=[
            {"role": "system", "content": "You are a guided meditation coach. Pleas include markup of format '[pause x]' where you include the x number of seconds to pause for (for example, used between an inhale and exhale) to make the script as accurate/good as possible. It can be varying amounts of seconds."},
            {"role": "user", "content": prompt}
          ]
        )


        script = completion.choices[0].message.content
        st.text_area("Generated Script", script, height=200)

        audio_path = process_script(script)
        st.success("Audio generated successfully!")

        with open(audio_path, 'rb') as audio_file:
            audio_bytes = audio_file.read()
            st.audio(audio_bytes, format='audio/mp3')

        os.remove(audio_path)  # Clean up temporary file after use
    else:
        st.error("Please enter both the API key and a prompt.")
