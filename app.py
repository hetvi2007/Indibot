import streamlit as st
import datetime
import uuid

# ---------------- Session State Setup ----------------
if "chats" not in st.session_state:
    st.session_state.chats = {}
if "archived_chats" not in st.session_state:
    st.session_state.archived_chats = {}
if "active_chat" not in st.session_state:
    st.session_state.active_chat = None

# ---------------- Helper Functions ----------------
def create_new_chat():
    chat_id = str(uuid.uuid4())[:8]
    st.session_state.chats[chat_id] = {
        "title": "Untitled",
        "messages": [],
        "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    st.session_state.active_chat = chat_id

def rename_chat(chat_id, new_title):
    st.session_state.chats[chat_id]["title"] = new_title

def delete_chat(chat_id):
    if chat_id in st.session_state.chats:
        del st.session_state.chats[chat_id]
        if st.session_state.active_chat == chat_id:
            st.session_state.active_chat = None

def archive_chat(chat_id):
    st.session_state.archived_chats[chat_id] = st.session_state.chats.pop(chat_id)
    if st.session_state.active_chat == chat_id:
        st.session_state.active_chat = None

# ---------------- Sidebar ----------------
st.sidebar.title("💬 Chats")

# New Chat Button
if st.sidebar.button("➕ New Chat"):
    create_new_chat()

# Search Chats
search_query = st.sidebar.text_input("🔍 Search chats")

# Active Chats List
for chat_id, chat in list(st.session_state.chats.items()):
    if search_query.lower() in chat["title"].lower():
        cols = st.sidebar.columns([5,1])
        if cols[0].button(chat["title"], key=f"open_{chat_id}"):
            st.session_state.active_chat = chat_id
        with cols[1].expander("⋮"):
            new_title = st.text_input("✏️ Rename", chat["title"], key=f"rename_{chat_id}")
            if new_title != chat["title"]:
                rename_chat(chat_id, new_title)
            if st.button("🗑️ Delete", key=f"delete_{chat_id}"):
                delete_chat(chat_id)
                st.experimental_rerun()
            if st.button("📦 Archive", key=f"archive_{chat_id}"):
                archive_chat(chat_id)
                st.experimental_rerun()

# Archived Section
if st.session_state.archived_chats:
    st.sidebar.subheader("📦 Archived")
    for chat_id, chat in st.session_state.archived_chats.items():
        if st.sidebar.button(chat["title"], key=f"arch_{chat_id}"):
            st.session_state.active_chat = chat_id

# ---------------- Main Area ----------------
if st.session_state.active_chat:
    st.write(f"### Active Chat: {st.session_state.chats[st.session_state.active_chat]['title']}")
else:
    st.write("👉 Select or create a chat from the sidebar.")
