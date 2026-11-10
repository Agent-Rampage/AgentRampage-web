import os
import io
import base64
import wave
import streamlit as st

from openai import OpenAI
from google import genai
from google.genai import types

st.set_page_config(
    page_title="Agent Rampage",
    page_icon="🤖",
    layout="wide"
)

# ---------------- SETTINGS ----------------

def get_setting(name, default=None):
    try:
        value = st.secrets.get(name, default)
    except Exception:
        value = None
    return value or os.getenv(name, default)


GROQ_API_KEY = get_setting("GROQ_API_KEY")
GROQ_MODEL = get_setting("GROQ_MODEL", "qwen/qwen3.8-27b")
GEMINI_API_KEY = get_setting("GEMINI_API_KEY")

MAX_TOKENS = 700
TTS_MODEL = "gemini-3.8-flash-tts"
TTS_VOICE = "Fenrir"

SYSTEM_PROMPT = """
You are Agent Rampage, a helpful AI assistant application.

Application creator: Naman.
Underlying AI model: Qwen, developed by Alibaba Group.
API provider: Groq.

When asked who created you, explain that Agent Rampage
was created by Naman and uses Qwen through Groq.

Use simple, natural English or Hinglish.
Keep answers concise unless more detail is requested.
Use plain text. Avoid unnecessary Markdown and LaTeX.
For physics numericals use:
Given
Formula
Calculation
Final Answer
"""

# ---------------- SESSION STATE ----------------

if "messages" not in st.session_state:
    st.session_state.messages = []

if "last_audio" not in st.session_state:
    st.session_state.last_audio = None

if "last_answer" not in st.session_state:
    st.session_state.last_answer = ""

if "voice_enabled" not in st.session_state:
    st.session_state.voice_enabled = True

if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

if "autoplay_audio" not in st.session_state:
    st.session_state.autoplay_audio = False

# ---------------- CLIENTS ----------------

if not GROQ_API_KEY:
    st.error("Groq API key is missing. Add it in Streamlit Secrets.")
    st.stop()

groq_client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1"
)

# ---------------- GEMINI SPEECH ----------------


def generate_speech(text):

    if not GEMINI_API_KEY:
        raise ValueError("Gemini API key is missing.")

    gemini_client = genai.Client(
        api_key=GEMINI_API_KEY
    )

    response = gemini_client.models.generate_content(
        model=TTS_MODEL,
        contents=text,
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=TTS_VOICE
                    )
                )
            )
        )
    )

    for part in response.parts:

        if part.inline_data and part.inline_data.data:

            pcm_data = part.inline_data.data

            # Convert raw audio into a WAV file
            audio_buffer = io.BytesIO()

            with wave.open(audio_buffer, "wb") as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(24000)
                wav_file.writeframes(pcm_data)

            return audio_buffer.getvalue()

    raise ValueError("Gemini returned no audio data.")

# ---------------- AI RESPONSE ----------------

def get_ai_response(messages):

    api_messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        }
    ]

    for message in messages:
        if message.get("image_data"):

            image_url = (
                "data:"
                + message["mime_type"]
                + ";base64,"
                + message["image_data"]
            )

            api_messages.append({
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": message["content"]
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_url
                        }
                    }
                ]
            })

        else:
            api_messages.append({
                "role": message["role"],
                "content": message["content"]
            })

    response = groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=api_messages,
        max_tokens=MAX_TOKENS,
        temperature=0.7
    )

    return response.choices[0].message.content or (
        "I could not generate a response."
    )


# ---------------- DESIGN ----------------

st.markdown("""
<style>
.stApp {
    background-color: #080d18;
    color: white;
}

h1 {
    color: #00ff88;
    text-align: center;
}

[data-testid="stSidebar"] {
    background-color: #101827;
}

.stChatMessage {
    border: 1px solid #263449;
    border-radius: 12px;
}

.stButton button {
    border-radius: 9px;
    border: 1px solid #00ff88;
}

</style>
""", unsafe_allow_html=True)

st.title("🤖 AGENT RAMPAGE")
st.caption("Your Personal AI Assistant")

# ---------------- SIDEBAR ----------------

with st.sidebar:

    st.title("⚙️ Settings")

    st.write("AI Model:", GROQ_MODEL)
    st.write("Speech Voice:", TTS_VOICE)

    st.session_state.voice_enabled = st.toggle(
        "🔊 Voice Output",
        value=st.session_state.voice_enabled
    )

    st.divider()

    if st.button("🔁 Replay Last Answer", use_container_width=True):
        if st.session_state.last_audio:
            st.session_state.autoplay_audio = True
        else:
            st.info("No previous audio available.")

    if st.button("⏹️ Stop Speaking", use_container_width=True):
        st.session_state.last_audio = None
        st.session_state.autoplay_audio = False
        st.rerun()

    if st.session_state.last_audio:
        st.audio(
            st.session_state.last_audio,
            format="audio/wav",
            autoplay=st.session_state.autoplay_audio
        )
        st.session_state.autoplay_audio = False

    st.divider()

    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.last_audio = None
        st.session_state.last_answer = ""
        st.session_state.autoplay_audio = False
        st.rerun()

    st.caption("Powered by Groq AI + Gemini TTS")


# ---------------- CHAT HISTORY ----------------

for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        st.write(message["content"])

        if message.get("image_data"):
            image_bytes = base64.b64decode(message["image_data"])
            st.image(image_bytes, use_container_width=True)


# ---------------- IMAGE UPLOAD ----------------

st.write("📷 Attach an image (optional)")

uploaded_image = st.file_uploader(
    "Upload an image",
    type=["png", "jpg", "jpeg"],
    key=f"image_{st.session_state.uploader_key}"
)

if uploaded_image:
    if uploaded_image.size > 10 * 1024 * 1024:
        st.error("Image must be smaller than 10 MB.")
        uploaded_image = None
    else:
        st.image(
            uploaded_image,
            caption="Image ready for Agent Rampage",
            use_container_width=True
        )


# ---------------- USER INPUT ----------------

prompt = st.chat_input("Ask Agent Rampage anything...")

if prompt:

    image_data = None
    mime_type = None

    if uploaded_image:
        image_data = base64.b64encode(
            uploaded_image.getvalue()
        ).decode("utf-8")

        mime_type = uploaded_image.type

    user_message = {
        "role": "user",
        "content": prompt,
        "image_data": image_data,
        "mime_type": mime_type
    }

    st.session_state.messages.append(user_message)

    with st.chat_message("user"):
        st.write(prompt)

        if image_data:
            st.image(
                base64.b64decode(image_data),
                use_container_width=True
            )

    with st.chat_message("assistant"):

        try:
            with st.spinner("Agent Rampage is thinking..."):

                answer = get_ai_response(
                    st.session_state.messages
                )

            st.write(answer)

            st.session_state.messages.append({
                "role": "assistant",
                "content": answer
            })

            st.session_state.last_answer = answer
            st.session_state.last_audio = None

            # Generate speech if voice output is enabled
            if st.session_state.voice_enabled:

                try:
                    with st.spinner("Generating Fenrir voice..."):

                        audio = generate_speech(answer)

                    st.session_state.last_audio = audio
                    st.audio(
                        audio,
                        format="audio/wav",
                        autoplay=True
                    )

                except Exception as speech_error:
                    st.warning(
                        "AI answer is ready, but speech generation "
                        f"failed: {speech_error}"
                    )

        except Exception as error:

            st.error(f"API Error: {error}")

            # Remove failed user request from history
            if st.session_state.messages:
                st.session_state.messages.pop()

    st.session_state.uploader_key += 1
