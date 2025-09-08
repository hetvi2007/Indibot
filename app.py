import os
import streamlit as st
from openai import OpenAI

# -------------------
# Page Config
# -------------------
st.set_page_config(
    page_title="Mehnitavi",
    page_icon="🤖",
    layout="wide"
)

# -------------------
# OpenAI Setup (safe)
# -------------------
api_key = st.secrets.get("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY"))
if not api_key:
    st.error("❌ No OpenAI API key found. Please set it in `.streamlit/secrets.toml` or environment variables.")
    st.stop()

client = OpenAI(api_key=api_key)

# -------------------
# Session State Setup
# -------------------
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "👋 Hello! I’m Mehnitavi, your AI assistant. How can I help you today?"}
    ]

# -------------------
# Chat Rendering
# -------------------
def render_messages():
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

st.title("🤖 Mehnitavi - AI Chatbot")

# Show past messages
render_messages()

# -------------------
# Chat Input
# -------------------
prompt = st.chat_input("Type your message...")

if prompt:
    # Save user message
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Query OpenAI
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=st.session_state.messages
    )

    reply = response.choices[0].message.content

    # Save assistant message
    st.session_state.messages.append({"role": "assistant", "content": reply})

    st.rerun()
