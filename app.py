# app.py
import os
import io
import base64
import uuid
from datetime import datetime

import streamlit as st
from groq import Groq

# ------------------------- App setup -------------------------
st.set_page_config(page_title="Mehnitavi", page_icon="🤖", layout="wide")

# Brand header
st.markdown(
    """
    <style>
    .brand { display:flex; align-items:center; gap:.6rem; }
    .brand .logo{font-size:1.6rem}
    .bubble { position:relative; padding:12px 14px; border-radius:14px; margin:4px 0 10px 0; }
    .bubble.user { background:#f2f5ff; border:1px solid #e3e8ff; }
    .bubble.assistant { background:#f7faf9; border:1px solid #ebf2ef; }
    .msg-tools { position:absolute; right:8px; top:8px; display:flex; gap:6px; }
    .msg-tools button { padding:2px 8px; font-size:.8rem; }
    .copy-btn { background:#f6f6f6; border:1px solid #e6e6e6; border-radius:8px; cursor:pointer; }
    .copy-ok { color:#2e7d32; font-weight:600; margin-left:6px; }
    .small-note { color:#6b7280; font-size:.85rem; }
    .file-pill { display:inline-flex; align-items:center; gap:.35rem; padding:.18rem .5rem; border-radius:999px;
                 background:#eef2ff; border:1px solid #e5e7ff; margin-right:.35rem; }
    </style>
    <div class="brand"><div class="logo">🤖</div><h1 style="margin:0">Mehnitavi</h1></div>
    """,
    unsafe_allow_html=True,
)

# ------------------------- API client -------------------------
API_KEY = os.environ.get("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY", "")
client = Groq(api_key=API_KEY) if API_KEY else None
MODEL = "llama-3.1-8b-instant"

# ------------------------- Session state -------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []   # [{id, role, content, files: [ {name, kind, note} ]}]
if "pending_edit" not in st.session_state:
    st.session_state.pending_edit = None  # message id being edited
if "last_files" not in st.session_state:
    st.session_state.last_files = []  # cache of uploaded file descriptors for the next turn


# ------------------------- Utilities -------------------------
def _uid() -> str:
    return uuid.uuid4().hex[:8]


def attach_file_descriptor(file) -> dict:
    """
    Create a lightweight descriptor for the uploaded file so the model
    can be told what was attached (no external parsers required).
    """
    name = file.name
    size = file.size
    ext = (name.split(".")[-1] or "").lower()
    kind = "audio" if ext in {"mp3", "wav", "m4a"} else "image" if ext in {"png", "jpg", "jpeg"} else "document"
    note = f"Attached {kind} file '{name}' ({size} bytes)."
    return {"name": name, "kind": kind, "note": note}


def render_copy_js(text: str, key: str):
    """
    Renders a compact 'Copy' button that copies `text` to clipboard (no extra libs).
    """
    payload = base64.b64encode(text.encode("utf-8")).decode("utf-8")
    html = f"""
    <script>
      function copy_{key}(){{
        const t = atob("{payload}");
        navigator.clipboard.writeText(t).then(() => {{
          const ok = document.getElementById("ok-{key}");
          if(ok) {{ ok.style.display = "inline"; setTimeout(() => ok.style.display="none", 1000); }}
        }});
      }}
    </script>
    <button class="copy-btn" onclick="copy_{key}()">Copy</button>
    <span id="ok-{key}" class="copy-ok" style="display:none;">Copied</span>
    """
    st.markdown(html, unsafe_allow_html=True)


def groq_chat(messages):
    """
    Call Groq chat completion safely.
    """
    if not client:
        return "⚠️ GROQ_API_KEY is missing. Add it to your secrets.toml or env."

    try:
        resp = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0.6,
        )
        return resp.choices[0].message.content
    except Exception as e:
        return f"⚠️ Error talking to Mehnitavi: {e}"


# ------------------------- Sidebar -------------------------
with st.sidebar:
    st.subheader("Options")
    if st.button("🆕 New chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.last_files = []
        st.session_state.pending_edit = None
        st.rerun()

    st.markdown("---")
    st.caption("Voice: upload an audio note. Mehnitavi will acknowledge it (no live mic dependency).")
    st.caption("Files: PDF/TXT/DOCX/PNG/JPG/MP3/WAV are accepted and referenced in the reply.")


# ------------------------- Chat history rendering -------------------------
for msg in st.session_state.messages:
    role = "user" if msg["role"] == "user" else "assistant"
    bubble_class = f"bubble {role}"

    with st.container():
        st.markdown(f'<div class="{bubble_class}">', unsafe_allow_html=True)

        # Copy + Edit/Regenerate tool row
        col_tools = st.columns([1, 9, 2])
        with col_tools[0]:
            pass
        with col_tools[1]:
            # Show message content
            st.markdown(msg["content"])
            # Show any file “pills”
            if msg.get("files"):
                pills = " ".join([f"<span class='file-pill'>📎 {f['name']}</span>" for f in msg["files"]])
                st.markdown(pills, unsafe_allow_html=True)
        with col_tools[2]:
            # Per-message tools
            render_copy_js(msg["content"], key=msg["id"])
            if msg["role"] == "user":
                if st.session_state.pending_edit == msg["id"]:
                    new_text = st.text_area("Edit message", value=msg["content"], key=f"edit-{msg['id']}")
                    col_e1, col_e2 = st.columns(2)
                    with col_e1:
                        if st.button("Save", key=f"save-{msg['id']}"):
                            msg["content"] = new_text
                            st.session_state.pending_edit = None
                            st.rerun()
                    with col_e2:
                        if st.button("Cancel", key=f"cancel-{msg['id']}"):
                            st.session_state.pending_edit = None
                            st.rerun()
                else:
                    if st.button("✏️ Edit", key=f"editbtn-{msg['id']}"):
                        st.session_state.pending_edit = msg["id"]
                        st.rerun()
            else:
                # Assistant: allow regenerate (re-run last prompt)
                if st.button("🔁 Regenerate", key=f"regen-{msg['id']}"):
                    # Find the last user message before this assistant message
                    idx = st.session_state.messages.index(msg)
                    # If the assistant's reply immediately follows a user prompt, regenerate from that context
                    history_for_model = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[:idx]]
                    new_reply = groq_chat(history_for_model)
                    msg["content"] = new_reply
                    st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

# ------------------------- Input row -------------------------
st.markdown("### ")
with st.container(border=True):
    st.write("**Upload attachments (optional)**")
    uploads = st.file_uploader(
        "Drag & drop files or browse",
        type=["png", "jpg", "jpeg", "pdf", "txt", "docx", "mp3", "wav", "m4a"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )

    # Attach uploaded files as descriptors (no external parsing libs)
    attached = []
    if uploads:
        for f in uploads:
            attached.append(attach_file_descriptor(f))
        st.session_state.last_files = attached

# Text prompt
user_text = st.chat_input("Ask Mehnitavi something…")

# ------------------------- Handle send -------------------------
if user_text:
    # 1) Add user message (with any queued file descriptors)
    user_msg = {"id": _uid(), "role": "user", "content": user_text, "time": datetime.now().isoformat()}
    if st.session_state.last_files:
        user_msg["files"] = st.session_state.last_files
    st.session_state.messages.append(user_msg)

    # 2) Build model messages (inject file notes into the user turn so model knows what was attached)
    model_turns = [{"role": "system", "content": "You are Mehnitavi, a helpful and concise assistant."}]
    for m in st.session_state.messages:
        content = m["content"]
        if m.get("files"):
            notes = "\n".join([f"- {f['note']}" for f in m["files"]])
            content = f"{content}\n\n[User attached files this turn]\n{notes}"
        model_turns.append({"role": m["role"], "content": content})

    # 3) Get assistant reply
    reply = groq_chat(model_turns)

    # 4) Append assistant message
    st.session_state.messages.append({"id": _uid(), "role": "assistant", "content": reply, "time": datetime.now().isoformat()})

    # 5) Clear queued files for next turn
    st.session_state.last_files = []

    st.rerun()

# ------------------------- Empty state -------------------------
if not st.session_state.messages:
    st.markdown(
        """
        <p class="small-note">
        Tip: you can attach PDFs, text, images, or audio notes. Mehnitavi will acknowledge attachments and answer using the message context.
        </p>
        """,
        unsafe_allow_html=True,
    )
