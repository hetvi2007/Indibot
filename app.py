import streamlit as st
import datetime
import pyperclip  # for copy-to-clipboard (install with `pip install pyperclip`)

# ---------------- Session State Setup ----------------
if "chats" not in st.session_state:
    st.session_state.chats = {}
if "archived_chats" not in st.session_state:
    st.session_state.archived_chats = {}
if "active_chat" not in st.session_state:
    st.session_state.active_chat = None
if "chat_counter" not in st.session_state:
    st.session_state.chat_counter = 0

# ---------------- Helper Functions ----------------
def create_new_chat():
    st.session_state.chat_counter += 1
    chat_id = f"chat_{st.session_state.chat_counter}"
    st.session_state.chats[chat_id] = {
        "title": f"Untitled {st.session_state.chat_counter}",
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

def share_chat(chat_id):
    chat = st.session_state.chats[chat_id]
    content = f"Chat: {chat['title']}\n\n"
    for msg in chat["messages"]:
        content += f"{msg['role'].capitalize()}: {msg['content']}\n"
    st.download_button("⬇️ Download Chat", content, file_name=f"{chat['title']}.txt")

# ---------------- Sidebar ----------------
st.sidebar.title("💬 Chat Manager")

# New Chat Button
if st.sidebar.button("➕ New Chat"):
    create_new_chat()

# Search Chats
search_query = st.sidebar.text_input("🔍 Search chats")

# Active Chats Section
st.sidebar.subheader("Active Chats")
for chat_id, chat in list(st.session_state.chats.items()):
    if search_query.lower() in chat["title"].lower():
        with st.sidebar.expander(chat["title"], expanded=False):
            if st.button("Open", key=f"open_{chat_id}"):
                st.session_state.active_chat = chat_id
            new_title = st.text_input("Rename", chat["title"], key=f"rename_{chat_id}")
            if new_title != chat["title"]:
                rename_chat(chat_id, new_title)
            if st.button("🗑️ Delete", key=f"delete_{chat_id}"):
                delete_chat(chat_id)
                st.experimental_rerun()
            if st.button("📦 Archive", key=f"archive_{chat_id}"):
                archive_chat(chat_id)
                st.experimental_rerun()
            share_chat(chat_id)

# Archived Chats Section
if st.session_state.archived_chats:
    st.sidebar.subheader("📦 Archived")
    for chat_id, chat in st.session_state.archived_chats.items():
        with st.sidebar.expander(chat["title"], expanded=False):
            if st.button("Restore", key=f"restore_{chat_id}"):
                st.session_state.chats[chat_id] = st.session_state.archived_chats.pop(chat_id)
                st.experimental_rerun()

# ---------------- Main Area ----------------
if st.session_state.active_chat:
    st.write(f"### Active Chat: {st.session_state.chats[st.session_state.active_chat]['title']}")
    st.write("💬 Messages will appear here later...")
else:
    st.write("👉 Select or create a chat from the sidebar.")
