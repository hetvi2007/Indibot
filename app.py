import streamlit as st
from datetime import datetime
import uuid
import os
from groq import Groq
from PIL import Image
import base64
import tempfile
import io
from streamlit_mic_recorder import mic_recorder, speech_to_text

# ---------- Setup ----------
st.set_page_config(page_title="Mehnitavi", page_icon="🤖", layout="wide")
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# ---------- Session ----------
store = st.session_state.setdefault("store", {"active": {}, "archived": {}})
current_id = st.session_state.setdefault("current_id", None)

# ---------- Helpers ----------
def new_chat():
    cid = uuid.uuid4().hex[:8]
    store["active"][cid] = {
        "title": "New Chat",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "messages": []
    }
    st.session_state.current_id = cid

def autotitle_if_needed(cid):
    chat = store["active"][cid]
    if chat["title"] == "New Chat":
        for m in chat["messages"]:
            if m["role"] == "user" and m["content"].strip():
                chat["title"] = m["content"].strip()[:40]
                break

# ---------- Sidebar ----------
with st.sidebar:
    st.header("Options")
    st.button("✍️ New chat", use_container_width=True, on_click=new_chat)

    if not store["active"]:
        st.caption("No chats yet.")
    else:
        for cid, chat in list(store["active"].items())[::-1]:
            if st.button(chat["title"] or "Untitled", key=f"open_{cid}", use_container_width=True):
                st.session_state.current_id = cid

# ---------- Main Chat ----------
st.title("🤖 Mehnitavi")

if current_id and current_id in store["active"]:
    chat = store["active"][current_id]

    # Display messages
    for m in chat["messages"]:
        with st.chat_message("user" if m["role"] == "user" else "assistant"):
            st.write(m["content"])

    # ---------- Input Bar ----------
    col1, col2, col3 = st.columns([6,1,1])

    with col1:
        text_input = st.chat_input("Ask anything…")

    with col2:
        audio_data = mic_recorder(start_prompt="🎤", stop_prompt="■", key="recorder")

    with col3:
        uploaded_file = st.file_uploader("📎", type=["png","jpg","jpeg","pdf","mp3","wav"], label_visibility="collapsed")

    # ---------- Handle Text ----------
    if text_input:
        chat["messages"].append({"role": "user", "content": text_input})
        try:
            response = client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[{"role": "system", "content": "You are Mehnitavi, a helpful assistant."}]
                         + chat["messages"],
            )
            reply = response.choices[0].message.content
        except Exception as e:
            reply = f"⚠️ Error: {e}"
        chat["messages"].append({"role": "assistant", "content": reply})
        autotitle_if_needed(current_id)
        st.rerun()

    # ---------- Handle Audio ----------
    if audio_data:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(audio_data["bytes"])
            tmp_path = tmp.name

        try:
            transcription = client.audio.transcriptions.create(
                model="whisper-large-v3",
                file=open(tmp_path, "rb")
            )
            user_text = transcription.text
        except Exception as e:
            user_text = f"⚠️ Error transcribing: {e}"

        chat["messages"].append({"role": "user", "content": f"(Voice) {user_text}"})
        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "system", "content": "You are Mehnitavi."}]
                     + chat["messages"],
        )
        reply = response.choices[0].message.content
        chat["messages"].append({"role": "assistant", "content": reply})
        st.rerun()

    # ---------- Handle Files ----------
    if uploaded_file:
        fname = uploaded_file.name
        if fname.lower().endswith((".png",".jpg",".jpeg")):
            img = Image.open(uploaded_file)
            st.image(img, caption=f"Uploaded: {fname}", use_container_width=True)
            chat["messages"].append({"role": "user", "content": f"📷 Sent image: {fname}"})
            # send image description
            reply = "Got your image! (Image analysis coming soon)"
        elif fname.lower().endswith(".pdf"):
            chat["messages"].append({"role": "user", "content": f"📄 Uploaded PDF: {fname}"})
            reply = "Got your PDF! (Can add PDF parsing here)"
        else:
            chat["messages"].append({"role": "user", "content": f"📎 Uploaded file: {fname}"})
            reply = "Got your file!"

        chat["messages"].append({"role": "assistant", "content": reply})
        st.rerun()

else:
    st.info("Start a new chat from the sidebar.")
