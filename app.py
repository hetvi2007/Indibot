import streamlit as st
import openai
import json
import os
import datetime

# ✅ New OpenAI client (v1.0+)
from openai import OpenAI

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# ✅ Page config
st.set_page_config(page_title="🤖 Smart Python Chatbot", layout="centered")
st.title("🤖 Smart Python Chatbot")
st.markdown("Chat with a smart assistant that remembers, stores, and adapts!")

# ✅ Persona selector
persona = st.selectbox("🧱 Choose Assistant Persona", [
    "Helpful Assistant",
    "Motivational Coach",
    "Tech Expert",
    "Comedian 🤡",
])

# ✅ Set system prompt
if "messages" not in st.session_state:
    system_msg = {
        "Helpful Assistant": "You are a helpful assistant.",
        "Motivational Coach": "You are a positive coach who inspires users.",
        "Tech Expert": "You are a Python coding assistant. Explain and fix code clearly.",
        "Comedian 🤡": "You are a funny chatbot who replies with jokes and humor.",
    }[persona]
    st.session_state.messages = [{"role": "system", "content": system_msg}]

# ✅ Display chat history
for msg in st.session_state.messages[1:]:
    if msg["role"] == "user":
        st.markdown(f"🧑 **You:** {msg['content']}")
    else:
        st.markdown(f"🤖 **Bot:** {msg['content']}")

# ✅ User input
user_input = st.text_input("💬 Type your message here:", key="input")

# ✅ Handle input and response
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.spinner("🤖 Thinking..."):
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=st.session_state.messages,
                temperature=0.7,
                max_tokens=500,
            )
            reply = response.choices[0].message.content
            st.session_state.messages.append({"role": "assistant", "content": reply})
            st.experimental_rerun()
        except Exception as e:
            st.error(f"❌ Error: {e}")

# ✅ Download chat
if st.button("💾 Download Chat (.txt & .json)"):
    history = st.session_state.messages[1:]
    chat_text = "\n".join(
        f"You: {m['content']}" if m["role"] == "user" else f"Bot: {m['content']}" for m in history
    )
    st.download_button("📄 TXT", chat_text, "chat.txt")
    st.download_button("🧾 JSON", json.dumps(history, indent=2), "chat.json")

# ✅ Save to local file
def save_chat_to_file():
    folder = "chat_logs"
    os.makedirs(folder, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(folder, f"chat_{timestamp}.json")
    with open(filepath, "w") as f:
        json.dump(st.session_state.messages, f, indent=2)

if st.button("🧠 Save Chat to Local File"):
    save_chat_to_file()
    st.success("Chat saved locally!")
