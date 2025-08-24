import streamlit as st
from groq import Groq

# Load API key from Streamlit Secrets
api_key = st.secrets["GROQ_API_KEY"]

# Initialize Groq client
client = Groq(api_key=api_key)

# Streamlit app
st.set_page_config(page_title="Groq Chatbot 🚀", page_icon="🤖")
st.title("🤖 Groq Chatbot")

# Session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "You are a helpful AI assistant."}
    ]

# Show chat history
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.chat_message("user").write(msg["content"])
    elif msg["role"] == "assistant":
        st.chat_message("assistant").write(msg["content"])

# Input box (new Streamlit chat_input)
if user_input := st.chat_input("Type your message..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.chat_message("user").write(user_input)

    try:
        # Call Groq API
        response = client.chat.completions.create(
            model="mixtral-8x7b-32768",   # You can change to other Groq models
            messages=st.session_state.messages
        )

        reply = response.choices[0].message.content

        # Add assistant reply
        st.session_state.messages.append({"role": "assistant", "content": reply})
        st.chat_message("assistant").write(reply)

    except Exception as e:
        st.error(f"Error: {e}")

