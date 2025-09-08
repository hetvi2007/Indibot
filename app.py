code working 03.09.2025                                                                                             import os
import streamlit as st
from groq import Groq

# ——— Page config ———
st.set_page_config(
    page_title="Mehnitavi (Groq-powered)",
    page_icon="🤖",
    layout="wide"
)

# ——— Groq API setup ———
groq_key = (
    st.secrets.get("GROQ_API_KEY") or
    os.getenv("GROQ_API_KEY")
)
if not groq_key:
    st.error(
        "❌ No Groq API key detected. "
        "Add it in .streamlit/secrets.toml or via environment variable."
    )
    st.stop()

client = Groq(api_key=groq_key)

# ——— Session state ———
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "👋 Hi, I’m Mehnitavi! Ask me anything."}
    ]

# ——— UI ———
st.title("🤖 Mehnitavi — AI ASSITANT ")
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input using ChatGPT style
prompt = st.chat_input("Type your message...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=st.session_state.messages
    )
    reply = response.choices[0].message.content
    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.rerun()
