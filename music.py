import os
import requests
import streamlit as st
import sounddevice as sd
from scipy.io.wavfile import write
from dotenv import load_dotenv
from yt_dlp import YoutubeDL

load_dotenv("RAPIDAPI_KEY.env")

RAPIDAPI_KEY = os.getenv('RAPIDAPI_KEY')
SHAZAM_API_URL = "https://shazam-api-free.p.rapidapi.com/shazam/recognize/"
HEADERS = {
    "X-RapidAPI-Key": RAPIDAPI_KEY,
    "X-RapidAPI-Host": "shazam-api-free.p.rapidapi.com"
}

DOWNLOAD_FOLDER = "downloaded_songs"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)


def record_audio(duration=5, sample_rate=44100, filename="temp_recording.wav"):
    st.info(f"Recording for {duration} seconds...")
    recording = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='int16')
    sd.wait()
    write(filename, sample_rate, recording)
    return filename


def identify_song(audio_file):
    try:
        with open(audio_file, 'rb') as f:
            files = {'upload_file': f}
            response = requests.post(SHAZAM_API_URL, headers=HEADERS, files=files)

        if response.status_code == 200:
            result = response.json()
            if 'track' in result:
                return result['track']
            else:
                return None
        else:
            st.error(f"Shazam API Error: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error during identification: {e}")
        return None


def download_song(track):
    if not track:
        return None

    search_query = f"{track['title']} {track['subtitle']} official audio"
    st.write(f"🔍 Searching YouTube for: {search_query}")

    try:
        with YoutubeDL({'format': 'bestaudio', 'outtmpl': f"{DOWNLOAD_FOLDER}/%(title)s.%(ext)s"}) as ydl:
            info = ydl.extract_info(f"ytsearch:{search_query}", download=True)['entries'][0]
            title = info.get('title', 'downloaded_song')
            return f"{DOWNLOAD_FOLDER}/{title}.webm"
    except Exception as e:
        st.error(f"Error downloading song: {e}")
        return None


# ==== Streamlit UI ====
st.set_page_config(page_title="Shazam Downloader", page_icon="🎧")

st.title("🎧 Shazam-Beat on every step")

if not RAPIDAPI_KEY:
    st.error("❌ RAPIDAPI_KEY not found in environment variables!")
    st.stop()

st.sidebar.title("Options")
duration = st.sidebar.slider("Recording Duration (seconds)", 3, 15, 5)
download_option = st.sidebar.checkbox("Download Song from YouTube", value=True)

if st.button("🎙️ Record & Identify"):
    audio_path = record_audio(duration)
    st.success("✅ Audio recorded. Identifying...")

    track = identify_song(audio_path)

    if track:
        st.success(f"🎵 Identified: {track['title']} by {track['subtitle']}")
        st.markdown(f"**Album:** {track.get('album', 'N/A')}")
        st.markdown(f"**Genre:** {track.get('genres', {}).get('primary', 'N/A')}")

        if download_option:
            with st.spinner("⬇️ Downloading song from YouTube..."):
                file_path = download_song(track)
                if file_path and os.path.exists(file_path):
                    st.audio(file_path)
                    st.success("✅ Song downloaded successfully!")
    else:
        st.warning("No match found by Shazam.")