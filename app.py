import streamlit as st
import json
import os
import uuid
from datetime import datetime

# File to store chats
CHAT_FILE = "chats.json"

# Load chats
def load_chats():
    if os.path.exists(CHAT_FILE):
        with open(CHAT_FILE, "r") as f:
            return json.load(f)
    return []

# Save chats
def save_chats(chats):
    with open(CHAT_FILE, "w") as f:
        json.dump(chats, f, indent=2)

# Create new chat
def new_chat():
    chats = load_chats()
    chat_id = str(uuid.uuid4())
    new_chat_data = {"id": chat_id, "created": datetime.now().isoformat(), "messages": []}
    chats.append(new_chat_data)
    save_chats(chats)
    st.session_state.current_chat = chat_id
    return chat_id

# Get chat by ID
def get_chat(chat_id):
    chats = load_chats()
    return next((c for c in chats if c["id"] == chat_id), None)

# Sidebar UI
st.sidebar.title("⚙️ Options")

if st.sidebar.button("➕ New Chat"):
    new_chat()

# Search bar
st.sidebar.subheader("🔍 Search in chat history")
search_query = st.sidebar.text_input("Search...")

if search_query:
    chats = load_chats()
    results = []

    for chat in chats:
        for msg in chat["messages"]:
            if search_query.lower() in msg["content"].lower():
                results.append({"chat_id": chat["id"], "preview": msg["content"][:50]})
                break  # only show once per chat

    if results:
        st.sidebar.markdown("### Search Results")
        for res in results:
            if st.sidebar.button(res["preview"], key=f"search_{res['chat_id']}"):
                st.session_state.current_chat = res["chat_id"]
    else:
        st.sidebar.write("No results found.")

# Main area
st.title("🤖 IndiBot")
st.caption("A simple chatbot built with Streamlit")

current_chat_id = st.session_state.get("current_chat")

if current_chat_id:
    chat = get_chat(current_chat_id)
    if chat:
        for msg in chat["messages"]:
            if msg["role"] == "user":
                st.chat_message("user").write(msg["content"])
            else:
                st.chat_message("assistant").write(msg["content"])

# Input box
if prompt := st.chat_input("Say something..."):
    if not current_chat_id:
        current_chat_id = new_chat()

    chats = load_chats()
    chat = get_chat(current_chat_id)

    # Add user msg
    chat["messages"].append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    # Dummy bot reply (replace with your model later)
    response = f"You said: {prompt}"
    chat["messages"].append({"role": "assistant", "content": response})
    st.chat_message("assistant").write(response)

    save_chats(chats)
