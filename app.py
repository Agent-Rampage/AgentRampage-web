
import os
import streamlit as st
from openai import OpenAI


# -----------------------------------------
# PAGE CONFIGURATION
# -----------------------------------------

st.set_page_config(
    page_title="Agent Rampage",
    page_icon="🤖",
    layout="centered"
)


# -----------------------------------------
# CONFIGURATION
# -----------------------------------------

def get_setting(name, default=None):
    """Read settings from Streamlit Secrets or environment variables."""
    try:
        value = st.secrets.get(name, default)
    except Exception:
        value = None

    return value or os.getenv(name, default)


GROQ_API_KEY = get_setting("GROQ_API_KEY")
GROQ_MODEL = get_setting(
    "GROQ_MODEL",
    "qwen/qwen3.8-27b"
)

MAX_TOKENS = 800


# -----------------------------------------
# AGENT RAMPAGE IDENTITY
# -----------------------------------------

SYSTEM_PROMPT = """
You are Agent Rampage, an AI assistant application created by Naman.

IDENTITY:
- Your application name is Agent Rampage.
- Your creator is Naman.
- You are an independent AI assistant project.
- Your language model is Qwen, developed by Alibaba Group.
- You access the model through the Groq API.
- You are not ChatGPT or an OpenAI product.

IMPORTANT IDENTITY RULES:
- Never confuse the application creator with the model developer.
- Never claim that Naman developed the underlying Qwen model.
- Never claim that Groq created the Agent Rampage application.

If someone asks "Who made you?", answer:
"I am Agent Rampage, an AI assistant application created by Naman.
My AI intelligence is powered by Qwen, developed by Alibaba Group,
and accessed through the Groq API."

If someone asks "Who created your AI model?", explain that
Qwen was developed by Alibaba Group.

RESPONSE STYLE:
- Use simple, natural language.
- Be friendly, helpful and conversational.
- Keep answers concise unless the user requests details.
- Support English and Hinglish.
- Do not unnecessarily mention your underlying model.
- Avoid excessive Markdown formatting.
"""


# -----------------------------------------
# GROQ CLIENT
# -----------------------------------------

client = None

if GROQ_API_KEY:
    client = OpenAI(
        api_key=GROQ_API_KEY,
        base_url="https://api.groq.com/openai/v1"
    )


# -----------------------------------------
# CUSTOM DESIGN
# -----------------------------------------

st.markdown("""
<style>

.stApp {
    background: #080d18;
    color: white;
}

.block-container {
    max-width: 850px;
    padding-top: 2rem;
}

h1, h2, h3, p, label {
    color: white;
}

[data-testid="stChatMessage"] {
    background-color: #111b2d;
    border: 1px solid #263650;
    border-radius: 15px;
    padding: 12px;
}

[data-testid="stChatInput"] {
    border-radius: 15px;
}

section[data-testid="stSidebar"] {
    background-color: #101827;
}

.stButton button {
    border-radius: 10px;
    border: 1px solid #34445e;
}

</style>
""", unsafe_allow_html=True)


# -----------------------------------------
# HEADER
# -----------------------------------------

st.title("🤖 Agent Rampage")

st.caption("Your AI assistant. Powered by Qwen through Groq.")

st.divider()


# -----------------------------------------
# CHAT HISTORY
# -----------------------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []


# Display previous messages

for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        st.markdown(message["content"])


# -----------------------------------------
# API KEY CHECK
# -----------------------------------------

if not GROQ_API_KEY:

    st.warning(
        "Groq API key is missing. "
        "Add GROQ_API_KEY in Streamlit Settings → Secrets."
    )


# -----------------------------------------
# CHAT INPUT
# -----------------------------------------

if prompt := st.chat_input(
    "Message Agent Rampage...",
    disabled=(client is None)
):

    # Save user message

    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    # Display user message

    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate AI response

    with st.chat_message("assistant"):

        response_placeholder = st.empty()

        try:

            api_messages = [
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                }
            ] + st.session_state.messages

            response = client.chat.completions.create(
                model=GROQ_MODEL,
                messages=api_messages,
                temperature=0.7,
                max_tokens=MAX_TOKENS
            )

            answer = response.choices[0].message.content

            if not answer:
                answer = "I couldn't generate a response. Please try again."

            response_placeholder.markdown(answer)

            # Save assistant response

            st.session_state.messages.append({
                "role": "assistant",
                "content": answer
            })

        except Exception as error:

            response_placeholder.error(
                "Agent Rampage encountered an API error."
            )

            st.caption(
                "Check your API key, model name and Groq account limits."
            )

            st.error(str(error))

            # Remove the unanswered user message
            # so it can be retried cleanly.

            if (
                st.session_state.messages
                and st.session_state.messages[-1]["role"] == "user"
            ):
                st.session_state.messages.pop()


# -----------------------------------------
# SIDEBAR
# -----------------------------------------

with st.sidebar:

    st.title("⚙️ Settings")

    st.write("🤖 Agent Rampage")

    st.write("AI Model:", GROQ_MODEL)

    st.divider()

    if st.button("🗑️ Clear Chat", use_container_width=True):

        st.session_state.messages = []

        st.rerun()

    st.divider()

    st.caption("Powered by Groq AI")

    st.caption("AI model: Qwen")

    st.caption("Created by Naman")


# -----------------------------------------
# END OF APPLICATION
# -----------------------------------------
