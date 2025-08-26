import streamlit as st
import json
import os
from datetime import datetime
from pathlib import Path

# -----------------------
# Storage
# -----------------------
CHAT_FILE = "chats.json"

def load_chats():
    if Path(CHAT_FILE).exists():
        with open(CHAT_FILE, "r") as f:
            return json.load(f)
    return {"active": {}, "archived": {}}

def save_chats(data):
    with open(CHAT_FILE, "w") as f:
        json.dump(data, f, indent=2)

# -----------------------
# Initialize session
# -----------------------
if "chats" not in st.session_state:
    st.session_state.chats = load_chats()
if "current_chat" not in st.session_state:
    st.session_state.current_chat = None

# -----------------------
# Sidebar
# -----------------------
st.sidebar.title("⚙️ Options")

# New Chat button
if st.sidebar.button("✍️ New Chat"):
    new_id = str(datetime.now().timestamp())
    st.session_state.chats["active"][new_id] = {
        "title": "New Chat",
        "messages": []
    }
    st.session_state.current_chat = new_id
    save_chats(st.session_state.chats)

# Search
search_query = st.sidebar.text_input("🔍 Search in chat history")

# Library (Archived)
with st.sidebar.expander("🗂️ Library"):
    for cid, chat in st.session_state.chats["archived"].items():
        st.write(chat["title"])

# -----------------------
# Active Chats list
# -----------------------
st.sidebar.subheader("Chats")
for cid, chat in st.session_state.chats["active"].items():
    cols = st.sidebar.columns([6, 1])
    if cols[0].button(chat["title"], key=f"chat_{cid}"):
        st.session_state.current_chat = cid

    # 3-dots menu
    with cols[1].popout():
        action = st.radio(
            "⋮",
            ["-", "Rename", "Delete", "Share", "Archive"],
            label_visibility="collapsed",
            key=f"action_{cid}"
        )
        if action == "Rename":
            new_name = st.text_input("Rename chat:", value=chat["title"], key=f"rename_{cid}")
            if st.button("Save", key=f"save_{cid}"):
                st.session_state.chats["active"][cid]["title"] = new_name
                save_chats(st.session_state.chats)
                st.rerun()
        elif action == "Delete":
            del st.session_state.chats["active"][cid]
            save_chats(st.session_state.chats)
            st.rerun()
        elif action == "Share":
            st.code(json.dumps(chat, indent=2))  # simple copy
        elif action == "Archive":
            st.session_state.chats["archived"][cid] = chat
            del st.session_state.chats["active"][cid]
            save_chats(st.session_state.chats)
            st.rerun()

# -----------------------
# Main Chat Window
# -----------------------
st.title("🤖 IndiBot")

if st.session_state.current_chat:
    chat = st.session_state.chats["active"].get(st.session_state.current_chat)
    if chat:
        for msg in chat["messages"]:
            st.write(f"**{msg['role']}**: {msg['content']}")

        # Input box
        user_input = st.chat_input("Say something...")
        if user_input:
            # Save user msg
            chat["messages"].append({"role": "You", "content": user_input})
            # Bot reply (dummy for now)
            bot_reply = f"Echo: {user_input}"
            chat["messages"].append({"role": "Bot", "content": bot_reply})

            # Auto title from first user msg
            if chat["title"] == "New Chat" and len(chat["messages"]) > 0:
                chat["title"] = chat["messages"][0]["content"][:20]

            save_chats(st.session_state.chats)
            st.rerun()
else:
    st.info("Start a new chat from the sidebar.")

