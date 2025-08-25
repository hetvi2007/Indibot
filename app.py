import streamlit as st
from groq import Groq

# -------------------- PAGE CONFIG --------------------
st.set_page_config(page_title="IndiBot", page_icon="🤖", layout="centered")

# -------------------- LOAD API KEY --------------------
API_KEY = st.secrets["GROQ_API_KEY"]
client = Groq(api_key=API_KEY)

# -------------------- SESSION STATE --------------------
if "messages" not in st.session_state:
    st.session_state.messages = []  # chat history

if "all_chats" not in st.session_state:
    st.session_state.all_chats = []  # stores past chat sessions


# -------------------- SIDEBAR --------------------
st.sidebar.header("⚙️ Options")

# New Chat
if st.sidebar.button("➕ New Chat"):
    if st.session_state.messages:
        st.session_state.all_chats.append(st.session_state.messages)
    st.session_state.messages = []
    st.rerun()

# Search Chats
search_query = st.sidebar.text_input("🔍 Search in chat history")
if search_query:
    st.sidebar.subheader("Search Results")
    for idx, chat in enumerate(st.session_state.all_chats):
        for msg in chat:
            if search_query.lower() in msg["content"].lower():
                st.sidebar.write(f"📝 Chat {idx+1}: {msg['role'].capitalize()} → {msg['content'][:50]}...")


# -------------------- MAIN TITLE --------------------
st.title("🤖 IndiBot")
st.write("A simple chatbot built with Streamlit + Groq API.")

# -------------------- DISPLAY CHAT --------------------
for message in st.session_state.messages:
    with st.chat_message("user" if message["role"] == "user" else "assistant"):
        st.markdown(message["content"])

# -------------------- USER INPUT --------------------
if user_input := st.chat_input("Say something..."):
    # Store user msg
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Display user msg
    with st.chat_message("user"):
        st.markdown(user_input)

    # Get Bot Response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = client.chat.completions.create(
                model="llama3-8b-8192",
                messages=st.session_state.messages,
                temperature=0.4,
            )
            bot_reply = response.choices[0].message.content
            st.markdown(bot_reply)

    # Save bot msg
    st.session_state.messages.append({"role": "assistant", "content": bot_reply})
