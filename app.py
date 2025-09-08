# app.py
import streamlit as st
from groq import Groq
import json
import os
import requests
import base64
from io import BytesIO
from urllib.parse import quote_plus

# -------------------- PAGE CONFIG --------------------
st.set_page_config(page_title="IndiBot", page_icon="🤖", layout="centered")

# -------------------- HISTORY STORAGE --------------------
HISTORY_FILE = "chat_history.json"

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)

# -------------------- INIT CLIENTS (SAFE) --------------------
# Groq (required for text chat)
try:
    GROQ_KEY = st.secrets["GROQ_API_KEY"]
except Exception:
    st.error("❌ Missing GROQ_API_KEY in Streamlit secrets. Add it in Settings → Secrets or .streamlit/secrets.toml")
    st.stop()

client = Groq(api_key=GROQ_KEY)

# OpenAI (optional) for image generation
OPENAI_KEY = st.secrets.get("OPENAI_API_KEY", None)

# -------------------- IMAGE GENERATION FUNCTION --------------------
def generate_image_openai(prompt):
    """
    Uses OpenAI Images endpoint if OPENAI_KEY available.
    Returns a dict: {"type":"image_url","content":url} or {"type":"image_b64","content":b64str} or None
    """
    if not OPENAI_KEY:
        return None

    try:
        url = "https://api.openai.com/v1/images/generations"
        headers = {
            "Authorization": f"Bearer {OPENAI_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "gpt-image-1",
            "prompt": prompt,
            "n": 1,
            "size": "1024x1024"
        }
        resp = requests.post(url, json=payload, headers=headers, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        # Try to extract url or base64
        if "data" in data and len(data["data"]) > 0:
            item = data["data"][0]
            if "b64_json" in item:
                return {"type": "image_b64", "content": item["b64_json"]}
            if "url" in item:
                return {"type": "image_url", "content": item["url"]}
        return None
    except Exception as e:
        # if image generation fails, return None so caller can fallback
        st.warning(f"Image generation failed: {e}")
        return None

def generate_image(prompt):
    # Try OpenAI first (if configured)
    result = generate_image_openai(prompt)
    if result:
        return result
    # fallback: placeholder image url
    placeholder = f"https://dummyimage.com/800x500/000/fff.png&text={quote_plus(prompt[:60])}"
    return {"type": "image_url", "content": placeholder}

# -------------------- SESSION STATE --------------------
if "messages" not in st.session_state:
    st.session_state.messages = []  # current conversation (list of {"role","content", optional "type"})

if "all_chats" not in st.session_state:
    st.session_state.all_chats = load_history()  # list of chats (each chat is list of messages)

if "current_chat_index" not in st.session_state:
    st.session_state.current_chat_index = None

# -------------------- SIDEBAR --------------------
st.sidebar.header("⚙️ Options")

# New Chat: save current chat (if any) and start fresh
if st.sidebar.button("➕ New Chat"):
    if st.session_state.messages:
        # append a copy of current messages to history
        st.session_state.all_chats.append(list(st.session_state.messages))
        save_history(st.session_state.all_chats)
    st.session_state.messages = []
    st.session_state.current_chat_index = None
    st.experimental_rerun()  # safe rerun

# Select past chat
st.sidebar.subheader("📂 Past Chats")
if st.session_state.all_chats:
    chat_labels = [f"Chat {i+1} — {len(chat)} msgs" for i, chat in enumerate(st.session_state.all_chats)]
else:
    chat_labels = []

selected_label = st.sidebar.selectbox("Select a chat to Open / Delete", ["-- Select --"] + chat_labels)

# Buttons: Open Selected / Delete Selected
col1, col2 = st.sidebar.columns([1,1])
with col1:
    if st.sidebar.button("Open Selected"):
        if selected_label != "-- Select --":
            idx = chat_labels.index(selected_label)
            st.session_state.messages = list(st.session_state.all_chats[idx])
            st.session_state.current_chat_index = idx
            st.experimental_rerun()
with col2:
    if st.sidebar.button("Delete Selected"):
        if selected_label != "-- Select --":
            idx = chat_labels.index(selected_label)
            # remove
            del st.session_state.all_chats[idx]
            save_history(st.session_state.all_chats)
            # reset if that chat was loaded
            if st.session_state.current_chat_index == idx:
                st.session_state.messages = []
                st.session_state.current_chat_index = None
            st.experimental_rerun()

# Search chats
st.sidebar.subheader("🔎 Search")
search_query = st.sidebar.text_input("Search across saved chats")
if search_query:
    st.sidebar.markdown("**Matches:**")
    found_any = False
    for ci, chat in enumerate(st.session_state.all_chats):
        for msg in chat:
            if search_query.lower() in msg.get("content", "").lower():
                found_any = True
                snippet = msg.get("content", "")[:80].replace("\n", " ")
                st.sidebar.write(f"Chat {ci+1} — {msg['role'].capitalize()}: {snippet}...")
                break
    if not found_any:
        st.sidebar.write("No matches found.")

# -------------------- MAIN UI --------------------
st.title("🤖 IndiBot")
st.write("A simple chatbot (Groq) with persistent history + image generation (optional).")

# Buttons in main area: Save current chat manually / Clear current chat
colA, colB = st.columns([1,1])
with colA:
    if st.button("💾 Save current chat"):
        if st.session_state.messages:
            st.session_state.all_chats.append(list(st.session_state.messages))
            save_history(st.session_state.all_chats)
            st.success("Chat saved.")
with colB:
    if st.button("🧹 Clear current chat"):
        st.session_state.messages = []
        st.session_state.current_chat_index = None
        st.experimental_rerun()

# Display messages
for msg in st.session_state.messages:
    role = msg.get("role", "assistant")
    if msg.get("type") == "image_url":
        st.chat_message(role)
        st.image(msg["content"], use_column_width=True)
    elif msg.get("type") == "image_b64":
        st.chat_message(role)
        try:
            img_bytes = base64.b64decode(msg["content"])
            st.image(BytesIO(img_bytes), use_column_width=True)
        except Exception:
            st.write("⚠️ Could not decode saved image.")
    else:
        # text message
        with st.chat_message(role):
            st.write(msg.get("content", ""))

# -------------------- INPUT HANDLING --------------------
user_input = st.chat_input("Say something... (use /image your prompt to generate image)")

if user_input:
    # add user message
    st.session_state.messages.append({"role": "user", "content": user_input})

    # display user message immediately
    with st.chat_message("user"):
        st.write(user_input)

    # image command
    if user_input.strip().lower().startswith("/image"):
        prompt = user_input.strip()[len("/image"):].strip()
        if not prompt:
            with st.chat_message("assistant"):
                st.write("Please provide a prompt after `/image`.")
        else:
            with st.chat_message("assistant"):
                with st.spinner("Generating image..."):
                    img_obj = generate_image(prompt)
                    if img_obj is None:
                        # fallback placeholder if generator returned None
                        placeholder = f"https://dummyimage.com/800x500/000/fff.png&text={quote_plus(prompt[:60])}"
                        st.image(placeholder, use_column_width=True)
                        st.session_state.messages.append({"role": "assistant", "content": placeholder, "type": "image_url"})
                    else:
                        if img_obj["type"] == "image_url":
                            st.image(img_obj["content"], use_column_width=True)
                            st.session_state.messages.append({"role": "assistant", "content": img_obj["content"], "type": "image_url"})
                        elif img_obj["type"] == "image_b64":
                            try:
                                img_bytes = base64.b64decode(img_obj["content"])
                                st.image(BytesIO(img_bytes), use_column_width=True)
                                st.session_state.messages.append({"role": "assistant", "content": img_obj["content"], "type": "image_b64"})
                            except Exception as e:
                                st.write("⚠️ Error showing image:", e)
    else:
        # Text chat -> send to Groq with full multi-turn (system prompt optional)
        system_prompt = "You are IndiBot, a helpful assistant."
        convo = [{"role": "system", "content": system_prompt}] + st.session_state.messages
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    resp = client.chat.completions.create(
                        model="llama3-8b-8192",
                        messages=convo,
                        temperature=0.4
                    )
                    bot_reply = resp.choices[0].message.content
                except Exception as e:
                    bot_reply = f"⚠️ Error contacting Groq: {e}"
                st.write(bot_reply)
                st.session_state.messages.append({"role": "assistant", "content": bot_reply})

    # After each exchange, update save (if editing an existing saved chat, update it)
    if st.session_state.current_chat_index is not None:
        st.session_state.all_chats[st.session_state.current_chat_index] = list(st.session_state.messages)
    else:
        # avoid duplicates: only append if not already last in all_chats
        if not st.session_state.all_chats or st.session_state.messages not in st.session_state.all_chats:
            # do not auto-append to all_chats every message; only save when user presses Save or New Chat
            pass
    save_history(st.session_state.all_chats)
