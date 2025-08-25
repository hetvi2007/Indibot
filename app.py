import streamlit as st
from groq import Groq
import os

# ---------------- SETUP ----------------
st.set_page_config(page_title="IndiBot", page_icon="🤖", layout="centered")

# Initialize Groq client safely
client = None
if API_KEY and API_KEY != "PASTE-YOUR-GROQ-API-KEY-HERE":
    try:
        client = Groq(api_key=API_KEY)
    except Exception as e:
        st.error(f"❌ Failed to initialize Groq client: {e}")
else:
    st.warning("⚠️ No valid Groq API key found. Please set one to continue.")

# ---------------- HEADER ----------------
st.title("🤖 IndiBot")
st.write("A smart chatbot built with **Streamlit** and **Groq**.")

# ---------------- CHAT HISTORY ----------------
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "system", "content": "You are IndiBot, a friendly assistant."}
    ]

# ---------------- USER INPUT ----------------
user_input = st.chat_input("Say something...")

if user_input and client:
    # Save user message
    st.session_state["messages"].append({"role": "user", "content": user_input})

    try:
        # Call Groq model
        response = client.chat.completions.create(
            model="mixtral-8x7b-32768",  # or "llama2-70b-4096"
            messages=st.session_state["messages"]
        )

        # Get bot reply
        bot_reply = response.choices[0].message.content

        # Save bot reply
        st.session_state["messages"].append({"role": "assistant", "content": bot_reply})

    except Exception as e:
        st.error(f"⚠️ Error while calling Groq API: {e}")

# ---------------- DISPLAY CHAT ----------------
for msg in st.session_state["messages"][1:]:  # skip system message
    if msg["role"] == "user":
        st.markdown(f"🧑 **You:** {msg['content']}")
    elif msg["role"] == "assistant":
        st.markdown(f"🤖 **IndiBot:** {msg['content']}")
