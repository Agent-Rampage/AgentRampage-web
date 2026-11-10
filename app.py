
import os
import streamlit as st
from openai import OpenAI

st.set_page_config(
    page_title="Agent Rampage",
    page_icon="🤖",
    layout="wide"
)

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
</style>
""", unsafe_allow_html=True)

st.title("🤖 AGENT RAMPAGE")
st.caption("Your Personal AI Assistant")

try:
    GROQ_API_KEY = st.secrets.get(
        "GROQ_API_KEY",
        os.getenv("GROQ_API_KEY")
    )
except Exception:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")

GROQ_MODEL = "qwen/qwen3.8-27b"

if "messages" not in st.session_state:
    st.session_state.messages = []

if not GROQ_API_KEY:
    st.warning("Please configure your Groq API key.")
    st.stop()

client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1"
)

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

prompt = st.chat_input("Ask Agent Rampage anything...")

if prompt:
    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        try:
            with st.spinner("Thinking..."):
                response = client.chat.completions.create(
                    model=GROQ_MODEL,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are Agent Rampage, a helpful AI assistant. "
                                "Answer clearly and concisely."
                            )
                        }
                    ] + st.session_state.messages,
                    max_tokens=800,
                    temperature=0.7
                )

                answer = response.choices[0].message.content

                if not answer:
                    answer = "I could not generate a response."

                st.write(answer)

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer
                })

        except Exception as error:
            st.error(f"API Error: {error}")

with st.sidebar:
    st.title("⚙️ Settings")
    st.write("Agent Rampage")
    st.write("Model:", GROQ_MODEL)

    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.rerun()

    st.caption("Powered by Groq AI")
