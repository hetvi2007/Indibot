import streamlit as st
from datetime import datetime
import uuid
import os
from groq import Groq
from PyPDF2 import PdfReader

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

def extract_file_content(uploaded_file):
    """Extract text from uploaded file"""
    if uploaded_file.type == "application/pdf":
        reader = PdfReader(uploaded_file)
        text = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
        return text or "📎 Uploaded empty PDF file"
    elif uploaded_file.type in ["text/plain", "application/json"]:
        return uploaded_file.read().decode("utf-8")
    else:
        return f"📎 Uploaded file: {uploaded_file.name}"

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
    for i, m in enumerate(chat["messages"]):
        with st.chat_message("user" if m["role"] == "user" else "assistant"):
            st.write(m["content"])

            # Toolbar only for assistant replies
            if m["role"] == "assistant":
                cols = st.columns(6)
                with cols[0]:
                    st.code(m["content"], language="markdown")  # copy button built-in
                with cols[1]:
                    st.button("👍 Like", key=f"like_{i}")
                with cols[2]:
                    st.button("👎 Dislike", key=f"dislike_{i}")
                with cols[3]:
                    st.button("🔊 Listen", key=f"listen_{i}")
                with cols[4]:
                    st.button("📤 Share", key=f"share_{i}")
                with cols[5]:
                    st.button("🔄 Regenerate", key=f"regen_{i}")

    # --- Input methods ---
    text = st.chat_input("Ask Mehnitavi something…")

    uploaded_file = st.file_uploader(
        "📎 Upload file",
        type=["png", "jpg", "jpeg", "pdf", "txt", "mp3", "wav"],
    )

    # Handle text input
    if text:
        chat["messages"].append({"role": "user", "content": text})

    # Handle file input
    if uploaded_file:
        file_content = extract_file_content(uploaded_file)
        chat["messages"].append({"role": "user", "content": file_content})

    # If any user input was given, get reply
    if text or uploaded_file:
        try:
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
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
