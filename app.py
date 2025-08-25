import streamlit as st
from groq import Groq

# Load API key from Streamlit secrets
API_KEY = st.secrets["GROQ_API_KEY"]

# Initialize Groq client
client = Groq(api_key=API_KEY)

# Streamlit UI
st.set_page_config(page_title="IndiBot", page_icon="🤖")
st.title("🤖 IndiBot")
st.write("A simple chatbot built with Streamlit and Groq API.")

# Session state for chat history
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# Chat input box
user_input = st.chat_input("Say something...")

if user_input:
    # Add user message
    st.session_state["messages"].append({"role": "user", "content": user_input})

    # Call Groq API
    response = client.chat.completions.create(
        model="llama3-8b-8192",  # Example model, you can change to another
        messages=st.session_state["messages"]
    )

    bot_reply = response.choices[0].message["content"]

    # Add bot reply
    st.session_state["messages"].append({"role": "assistant", "content": bot_reply})

# Display chat history
for msg in st.session_state["messages"]:
    if msg["role"] == "user":
        st.markdown(f"🧑 **You**: {msg['content']}")
    else:
        st.markdown(f"🤖 **IndiBot**: {msg['content']}")
