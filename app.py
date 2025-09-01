import streamlit as st
from datetime import datetime
import uuid
import os
from groq import Groq
from streamlit_mic_recorder import mic_recorder, speech_to_text

# ----------------- PAGE CONFIG -----------------
st.set_page_config(page_title="Mehnitavi", page_icon="🤖", layout="wide")

# ----------------- STYLE FIXES -----------------
st.markdown("""
    <style>
    /* Hide drag-drop area + extra file uploader text */
    div[data-testid="stFileUploaderDropzone"] {display: none;}
    div[data-testid="stFileUploader"] section {display: none;}
    div[data-testid="stFileUploader"] small {display: none;}
    </style>
""", unsafe_allow_html=True)

# ----------------- INIT CLIENT -----------------
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# ----------------- SESSION STORE -----------------
store = st.session_state.setdefault("store", {"active": {}, "archived": {}})
current_id = st.session_state.setdefault("current_id", None)

# ----------------- HELPERS -----------------
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

# ----------------- SIDEBAR -----------------
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

# ----------------- MAIN AREA -----------------
st.title("🤖 Mehnitavi")

if current_id and current_id in store["active"]:
    chat = store["active"][current_id]

    # Show chat history
    for m in chat["messages"]:
        with st.chat_message("user" if m["role"] == "user" else "assistant"):
            st.markdown(m["content"])
            if m["role"] == "assistant":
                st.markdown(
                    """
                    <div style='display: flex; gap: 15px; margin-top: 5px; font-size: 18px; color: gray;'>
                        <span title='Copy'>📋</span>
                        <span title='Like'>👍</span>
                        <span title='Dislike'>👎</span>
                        <span title='Speak'>🔊</span>
                        <span title='Share'>⤴️</span>
                        <span title='Refresh'>🔄</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    # --- Input row (upload + chat + mic) ---
    col1, col2, col3 = st.columns([0.1, 0.7, 0.2])

    with col1:
        uploaded_file = st.file_uploader(
            "📎",
            type=["png", "jpg", "jpeg", "pdf", "txt", "mp3", "wav"],
            label_visibility="collapsed"
        )

    with col2:
        text = st.chat_input("Ask Mehnitavi something…")

    with col3:
        voice = mic_recorder(
            start_prompt="🎤 Record",
            stop_prompt="⏹️ Stop",
            just_once=True,
            use_container_width=True,
            key="voice_recorder"
        )

    # Handle text
    if text:
        chat["messages"].append({"role": "user", "content": text})

    # Handle voice
    if voice:
        chat["messages"].append({"role": "user", "content": speech_to_text(voice)})

    # Handle file
    if uploaded_file:
        chat["messages"].append({"role": "user", "content": f"📎 Uploaded file: {uploaded_file.name}"})

    # Send to LLM
    if text or voice or uploaded_file:
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
