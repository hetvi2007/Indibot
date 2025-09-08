import streamlit as st
import datetime
import pyperclip
from openai import OpenAI

# ------------------- OpenAI Client -------------------
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# ------------------- Session State -------------------
if "chats" not in st.session_state:
    st.session_state.chats = {}
if "active_chat" not in st.session_state:
    st.session_state.active_chat = None
if "chat_counter" not in st.session_state:
    st.session_state.chat_counter = 0

# ------------------- Helper Functions ----------------
def create_new_chat():
    st.session_state.chat_counter += 1
    chat_id = f"chat_{st.session_state.chat_counter}"
    st.session_state.chats[chat_id] = {
        "title": f"Untitled {st.session_state.chat_counter}",
        "messages": [],
        "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    st.session_state.active_chat = chat_id

def get_ai_response(messages):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages
    )
    return response.choices[0].message.content

# ------------------- Sidebar -------------------
st.sidebar.title("🤖 Mehnitavi")

if st.sidebar.button("➕ New Chat"):
    create_new_chat()

if st.session_state.chats:
    for cid, chat in st.session_state.chats.items():
        if st.sidebar.button(chat["title"], key=cid):
            st.session_state.active_chat = cid

# ------------------- Main Area -------------------
if st.session_state.active_chat:
    chat = st.session_state.chats[st.session_state.active_chat]

    st.title(f"💬 {chat['title']}")

    # Render chat messages
    for msg in chat["messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat input
    user_input = st.chat_input("Type your message...")
    if user_input:
        # Add user message
        chat["messages"].append({"role": "user", "content": user_input})

        # Get AI response
        ai_reply = get_ai_response(chat["messages"])
        chat["messages"].append({"role": "assistant", "content": ai_reply})

        st.experimental_rerun()

else:
    st.write("👉 Create or open a chat from the sidebar.")
