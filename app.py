import streamlit as st
import json
import os

# File where chats are stored
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

# Sidebar layout
def sidebar():
    st.sidebar.title("Options")

    # Load existing chats
    chats = load_chats()

    # New chat button
    if st.sidebar.button("➕ New Chat"):
        new_chat = {"id": len(chats) + 1, "title": f"Chat {len(chats) + 1}", "messages": []}
        chats.append(new_chat)
        save_chats(chats)
        st.session_state.active_chat = new_chat["id"]

    # Show chat list
    st.sidebar.subheader("Past Chats")
    for chat in chats:
        with st.sidebar.expander(chat["title"], expanded=False):
            if st.button("Open", key=f"open_{chat['id']}"):
                st.session_state.active_chat = chat["id"]

            if st.button("Rename", key=f"rename_{chat['id']}"):
                new_title = st.text_input("New title:", key=f"title_{chat['id']}")
                if new_title:
                    chat["title"] = new_title
                    save_chats(chats)

            if st.button("🗑 Delete", key=f"delete_{chat['id']}"):
                chats = [c for c in chats if c["id"] != chat["id"]]
                save_chats(chats)
                st.rerun()

            if st.button("📦 Archive", key=f"archive_{chat['id']}"):
                chat["archived"] = True
                save_chats(chats)

            if st.button("📤 Share", key=f"share_{chat['id']}"):
                st.code(json.dumps(chat, indent=2), language="json")

    return chats

# Main app
def main():
    st.title("🤖 IndiBot")
    st.write("A simple chatbot built with Streamlit + Groq API.")

    chats = sidebar()

    # Find active chat
    active_chat_id = st.session_state.get("active_chat")
    active_chat = next((c for c in chats if c["id"] == active_chat_id), None)

    if active_chat:
        st.subheader(f"Chat: {active_chat['title']}")
        for msg in active_chat["messages"]:
            st.write(msg)

        user_input = st.chat_input("Say something...")
        if user_input:
            active_chat["messages"].append(f"You: {user_input}")
            active_chat["messages"].append(f"Bot: [reply to '{user_input}']")
            save_chats(chats)
            st.rerun()

if __name__ == "__main__":
    main()
