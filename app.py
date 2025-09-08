import streamlit as st
import openai

# --- Streamlit page config ---
st.set_page_config(page_title="Smart Chatbot", page_icon="🤖", layout="centered")

st.markdown("""
    <style>
    .stChatMessage {
        background-color: #f0f2f6;
        padding: 12px 16px;
        border-radius: 12px;
        margin-bottom: 10px;
        max-width: 85%;
    }
    .user-message {
        background-color: #DCF8C6;
        margin-left: auto;
        text-align: right;
    }
    .ai-message {
        background-color: #F1F0F0;
        margin-right: auto;
        text-align: left;
    }
    .chat-container {
        height: 400px;
        overflow-y: auto;
        padding: 10px;
        border: 1px solid #ccc;
        border-radius: 10px;
        margin-bottom: 15px;
        background-color: #fff;
    }
    </style>
""", unsafe_allow_html=True)

# --- Title ---
st.title("🤖 Smart Chatbot")
st.subheader("Talk to an intelligent assistant that responds with purpose.")

# --- Chat history ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Chat Display ---
chat_container = st.container()
with chat_container:
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    for msg in st.session_state.messages:
        class_name = "user-message" if msg["role"] == "user" else "ai-message"
        st.markdown(f'<div class="stChatMessage {class_name}">{msg["content"]}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- Input ---
user_input = st.text_input("Your Message", placeholder="Type something and hit Enter...")

# --- Handle input ---
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Simulate AI response (replace this with OpenAI call)
    ai_response = f"I'm thinking about: '{user_input}' — how can I help more specifically?"

    st.session_state.messages.append({"role": "assistant", "content": ai_response})
    st.experimental_rerun()
