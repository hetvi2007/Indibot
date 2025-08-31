import streamlit as st
from datetime import datetime
import uuid
import os
from groq import Groq
from PIL import Image
import base64
import tempfile
import io

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

def rename_chat(cid, new_title, bucket="active"):
    if new_title.strip():
        store[bucket][cid]["title"] = new_title.strip()

def delete_chat(cid, bucket="active"):
    store[bucket].pop(cid, None)
    if bucket == "active" and st.session_state.current_id == cid:
        st.session_state.current_id = None

def archive_chat(cid):
    store["archived"][cid] = store["active"].pop(cid)
    if st.session_state.current_id == cid:
        st.session_state.current_id = None

def restore_chat(cid):
    store["active"][cid] = store["archived"].pop(cid)

def export_text(cid, bucket="active"):
    chat = store[bucket][cid]
    lines = [f"Title: {chat['title']}", f"Created: {chat['created_at']}", "-"*40]
    for m in chat["messages"]:
        lines.append(f"{m['role'].capitalize()}: {m['content']}")
    return "\n".join(lines)

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

    # Active chats
    if not store["active"]:
        st.caption("No chats yet. Start one!")
    else:
        for cid, chat in list(store["active"].items())[::-1]:
            c1, c2 = st.columns([0.8, 0.2])
            if c1.button(chat["title"] or "Untitled", key=f"open_{cid}", use_container_width=True):
                open_chat(cid)
            with c2:
                with st.popover("⋮"):
                    new_name = st.text_input("Rename", value=chat["title"], key=f"rn_{cid}")
                    if st.button("💾 Save name", key=f"rns_{cid}"):
                        rename_chat(cid, new_name, bucket="active")
                    st.download_button(
                        "⬇️ Download (.txt)",
                        data=export_text(cid, bucket="active"),
                        file_name=f"{(chat['title'] or 'chat')}.txt",
                        key=f"dl_{cid}",
                        use_container_width=True,
                    )
                    if st.button("📦 Archive", key=f"arc_{cid}"):
                        archive_chat(cid)
                    if st.button("🗑️ Delete", key=f"del_{cid}"):
                        delete_chat(cid, bucket="active")

    # Archived chats
    if store["archived"]:
        with st.expander("🗂️ Library"):
            for cid, chat in list(store["archived"].items())[::-1]:
                c1, c2 = st.columns([0.8, 0.2])
                c1.write(f"📄 {chat['title'] or 'Untitled'}")
                with c2:
                    with st.popover("⋮"):
                        new_name = st.text_input("Rename", value=chat["title"], key=f"arn_{cid}")
                        if st.button("💾 Save name", key=f"arns_{cid}"):
                            rename_chat(cid, new_name, bucket="archived")
                        st.download_button(
                            "⬇️ Download (.txt)",
                            data=export_text(cid, bucket="archived"),
                            file_name=f"{(chat['title'] or 'chat')}.txt",
                            key=f"adl_{cid}",
                            use_container_width=True,
                        )
                        if st.button("↩️ Restore", key=f"res_{cid}"):
                            restore_chat(cid)
                        if st.button("🗑️ Delete", key=f"adel_{cid}"):
                            delete_chat(cid, bucket="archived")

# ---------- Main Area ----------
st.title("🤖 Mehnitavi")

if current_id and current_id in store["active"]:
    chat = store["active"][current_id]

    # show messages
    for m in chat["messages"]:
        with st.chat_message("user" if m["role"] == "user" else "assistant"):
            st.write(m["content"])

    # ---- Inputs ----
    col1, col2, col3 = st.columns([3,1,1])

    with col1:
        text = st.chat_input("Ask Mehnitavi something…")

    with col2:
        uploaded_img = st.file_uploader("📷 Upload Image", type=["png", "jpg", "jpeg"], label_visibility="collapsed")

    with col3:
        audio_file = st.file_uploader("🎤 Upload Voice", type=["wav", "mp3", "m4a"], label_visibility="collapsed")

    # ---- Handle text ----
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
            reply = f"⚠️ Error: {e}"
        chat["messages"].append({"role": "assistant", "content": reply})
        autotitle_if_needed(current_id)
        st.rerun()

    # ---- Handle image ----
    if uploaded_img:
        img = Image.open(uploaded_img)
        st.image(img, caption="Uploaded Image", use_container_width=True)
        chat["messages"].append({"role": "user", "content": "📷 Sent an image."})

        try:
            # Convert image to base64
            buffered = io.BytesIO()
            img.save(buffered, format="PNG")
            img_b64 = base64.b64encode(buffered.getvalue()).decode()

            response = client.chat.completions.create(
                model="llama3-8b-8192",  # If Groq supports multimodal
                messages=[
                    {"role": "system", "content": "You are Mehnitavi, a helpful assistant that can also analyze images."},
                    {"role": "user", "content": f"Here’s an image (base64): {img_b64}. Please describe it."}
                ],
            )
            reply = response.choices[0].message.content
        except Exception as e:
            reply = f"⚠️ Error analyzing image: {e}"

        chat["messages"].append({"role": "assistant", "content": reply})
        st.rerun()

    # ---- Handle audio ----
    if audio_file:
        chat["messages"].append({"role": "user", "content": "🎤 Sent a voice message."})
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                tmp.write(audio_file.read())
                tmp_path = tmp.name

            # Transcribe audio
            transcription = client.audio.transcriptions.create(
                model="whisper-large-v3",
                file=open(tmp_path, "rb")
            )
            user_text = transcription.text
            chat["messages"].append({"role": "user", "content": f"(Voice) {user_text}"})

            # Get reply
            response = client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[{"role": "system", "content": "You are Mehnitavi, a helpful assistant."}]
                         + chat["messages"],
            )
            reply = response.choices[0].message.content
        except Exception as e:
            reply = f"⚠️ Error transcribing audio: {e}"

        chat["messages"].append({"role": "assistant", "content": reply})
        st.rerun()

else:
    st.info("Start a new chat from the sidebar.")
