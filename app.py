import os
import streamlit as st
from groq import Groq

# ——— Page config ———
st.set_page_config(
    page_title="Mehnitavi (Groq-powered)",
    page_icon="🤖",
    layout="wide"
)

# ——— Groq API setup ———
groq_key = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")

if not groq_key:
    st.error("❌ No Groq API key detected. Add it in .streamlit/secrets.toml or via environment variable.")
    st.stop()

client = Groq(api_key=groq_key)

# ——— Session state ———
if "messages" not in st.session_state or not isinstance(st.session_state.messages, list):
    st.session_state.messages = [
        {"role": "assistant", "content": "👋 Hi, I’m Mehnitavi (Groq)! Ask me anything."}
    ]

# ——— UI ———
st.title("🤖 Mehnitavi — Groq Cloud Chatbot")

for msg in st.session_state.messages:
    with st.chat_message(msg.get("role", "assistant")):
        st.markdown(str(msg.get("content", "")))

# Chat input
prompt = st.chat_input("Type your message...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})

    # ——— Call Groq API safely ———
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=st.session_state.messages
        )
        # Check if response structure exists
        if response and hasattr(response, "choices") and len(response.choices) > 0:
            reply = response.choices[0].message.content
        else:
            reply = "❌ Groq returned an empty response."
    except Exception as e:
        reply = f"❌ Failed to get response from Groq API: {str(e)}"

    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.rerun()
