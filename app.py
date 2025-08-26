import streamlit as st
from groq import Groq
import json
import os
import requests

# -------------------- PAGE CONFIG --------------------
st.set_page_config(page_title="IndiBot", page_icon="🤖", layout="centered")

# -------------------- LOAD API KEY --------------------
API_KEY = st.secrets["GROQ_API_KEY"]
client = Groq(api_key=API_KEY)

# -------------------- HISTORY STORAGE --------------------
HISTORY_FILE = "chat_history.json"

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    return []

def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)

# -------------------- SESSION STATE --------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "all_chats" not in st.session_state:
    st.session_state.all_chats = load_history()

if "current_chat_index" not in st.session_state:
    st.session_state.current_chat_index = None

# -------------------- SIDEBAR --------------------
st.sidebar.header("⚙️ Options")

# New Chat
if st.sidebar.button("➕ New Chat"):
    if st.session_state.messages:
        st.session_state.all_chats.append(st.session_state.messages)
        save_history(st.session_state.all_chats)
    st.session_state.messages = []
    st.session_state.current_chat_index = None
    st.rerun()

# Search Chats
search_query = st.sidebar.text_input("🔍 Search in chat history")
if search_query:
    st.sidebar.subheader("Search Results")
    for idx, chat in enumerate(st.session_state.all_chats):
        for msg in chat:
            if search_query.lower() in msg["content"].lower():
                st.sidebar.write(f"📝 Chat {idx+1}: {msg['role'].capitalize()} → {msg['content'][:50]}...")

# View Past Chats
st.sidebar.subheader("📂 Past Chats")
if st.session_state.all_chats:
    for i, chat in enumerate(st.session_state.all_chats):
        col1, col2 = st.sidebar.columns([4,1])
        with col1:
            if st.sidebar.button(f"Open Chat {i+1}", key=f"open_{i}"):
                st.session_state.messages = chat.copy()
                st.session_state.current_chat_index = i
                st.rerun()
        with col2:
            if st.sidebar.button("❌", key=f"delete_{i}"):
                del st.session_state.all_chats[i]
                save_history(st.session_state.all_chats)
                st.session_state.messages = []
                st.session_state.current_chat_index = None
                st.rerun()

# -------------------- MAIN TITLE --------------------
st.title("🤖 IndiBot")
st.write("A chatbot with **Groq AI + Image Generation** 🚀")

# -------------------- DISPLAY CHAT --------------------
for message in st.session_state.messages:
    with st.chat_message("user" if message["role"] == "user" else "assistant"):
        if message.get("type") == "image":
            st.image(message["content"], caption="Generated Image")
        else:
            st.markdown(message["content"])

# -------------------- USER INPUT --------------------
if user_input := st.chat_input("Say something..."):
    # Handle Image Requests
    if user_input.startswith("/image"):
        prompt = user_input.replace("/image", "").strip()
        st.session_state.messages.append({"role": "user", "content": user_input})

        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("🎨 Generating image..."):
                # Example: using Dummy placeholder image generator (replace with real API)
                image_url = f"https://dummyimage.com/600x400/000/fff.png&text={prompt.replace(' ','+')}"
                st.image(image_url, caption=prompt)

        st.session_state.messages.append({"role": "assistant", "content": image_url, "type": "image"})

    else:
        # Normal Text Chat
        st.session_state.messages.append({"role": "user", "content": user_input})

        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = client.chat.completions.create(
                    model="llama3-8b-8192",
                    messages=st.session_state.messages,
                    temperature=0.4,
                )
                bot_reply = response.choices[0].message.content
                st.markdown(bot_reply)

        st.session_state.messages.append({"role": "assistant", "content": bot_reply})

    # Update history
    if st.session_state.current_chat_index is not None:
        st.session_state.all_chats[st.session_state.current_chat_index] = st.session_state.messages
    else:
        if st.session_state.messages not in st.session_state.all_chats:
            st.session_state.all_chats.append(st.session_state.messages)

    save_history(st.session_state.all_chats)
