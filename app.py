import json
import streamlit as st
import os

# Load chats
def load_chats():
    if os.path.exists("chats.json"):
        with open("chats.json", "r") as f:
            return json.load(f)
    return []

def save_chats(chats):
    with open("chats.json", "w") as f:
        json.dump(chats, f, indent=2)

# Sidebar search
st.sidebar.subheader("🔍 Search chats")
query = st.sidebar.text_input("Search in chat history")

if query:
    chats = load_chats()
    results = []
    for i, chat in enumerate(chats):
        # Search in messages
        if any(query.lower() in msg["content"].lower() for msg in chat["messages"]):
            results.append((i, chat))

    if results:
        st.sidebar.write("### Search Results")
        for idx, chat in results:
            label = chat["messages"][0]["content"][:40] + "..." if chat["messages"] else f"Chat {idx+1}"
            if st.sidebar.button(label, key=f"search_{idx}"):
                st.session_state.current_chat = idx
                st.rerun()
    else:
        st.sidebar.write("No results found ❌")
