import streamlit as st
from datetime import datetime
import uuid
import os
from groq import Groq

# ---------- Setup ----------
st.set_page_config(page_title="Mehnitavi", page_icon="🤖", layout="wide")

# Initialize Groq client
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# ---------- Session Store ----------
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

def open_chat(cid):
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

    st.markdown("---")
    st.subheader("Chats")
    if not store["active"]:
        st.caption("No chats yet. Start one!")
    else:
        for cid, chat in list(store["active"].items())[::-1]:
            if st.button(chat["title"] or "Untitled", key=f"open_{cid}", use_container_width=True):
                open_chat(cid)

# ---------- Main Area ----------
st.title("🤖 Mehnitavi")

if current_id and current_id in store["active"]:
    chat = store["active"][current_id]

    # show messages
    for m in chat["messages"]:
        with st.chat_message("user" if m["role"] == "user" else "assistant"):
            st.write(m["content"])

    # --- Input system ---
    text = st.chat_input("Ask Mehnitavi something…")

    # File uploader (images, pdfs, text, audio)
    uploaded_file = st.file_uploader(
        "📎 Upload file (images, PDFs, text, or voice notes)", 
        type=["png", "jpg", "jpeg", "pdf", "txt", "mp3", "wav"]
    )

    if uploaded_file:
        file_msg = f"📎 Uploaded file: {uploaded_file.name}"
        chat["messages"].append({"role": "user", "content": file_msg})
        st.success(f"File `{uploaded_file.name}` uploaded!")

    # --- Handle text input ---
    if text:
        chat["messages"].append({"role": "user", "content": text})
        try:
            response = client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[{"role": "system", "content": "You are Mehnitavi, a helpful assistant."}]
                         + chat["messages"],
            )
            reply = response.choices[0].message.content
        except Exception as e:
            reply = f"⚠️ Error talking to Mehnitavi: {e}"
        chat["messages"].append({"role": "assistant", "content": reply})
        autotitle_if_needed(current_id)
        st.rerun()

else:
    st.info("Start a new chat from the sidebar.")
