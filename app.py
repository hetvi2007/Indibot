# app.py
import streamlit as st
from datetime import datetime
import uuid
import os

# optional dependencies (graceful)
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except Exception:
    GROQ_AVAILABLE = False

try:
    from PyPDF2 import PdfReader
    PDF_AVAILABLE = True
except Exception:
    PDF_AVAILABLE = False

# ----------------- Config -----------------
st.set_page_config(page_title="Mehnitavi", page_icon="🤖", layout="wide")
MODEL = "llama-3.1-8b-instant"

# init client only if available and key present
API_KEY = os.environ.get("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY", "") if "secrets" in st.__dict__ else ""
client = Groq(api_key=API_KEY) if GROQ_AVAILABLE and API_KEY else None

# ----------------- Utilities -----------------
def _uid():
    return uuid.uuid4().hex[:8]

def render_copy_js(text: str, key: str):
    """Render a small Copy button using JS (works in browser)."""
    payload = (text or "").replace("\\", "\\\\").replace("'", "\\'")
    html = f"""
    <script>
    function copyToClipboard_{key}(){{
      navigator.clipboard.writeText('{payload}');
      const ok = document.getElementById("ok-{key}");
      if(ok) {{ ok.style.display = "inline"; setTimeout(()=>ok.style.display="none", 900); }}
    }}
    </script>
    <button onclick="copyToClipboard_{key}()" style="padding:6px;border-radius:6px;border:1px solid #ddd;background:#fafafa;cursor:pointer">📋 Copy</button>
    <span id="ok-{key}" style="display:none;color:green;font-weight:600;margin-left:6px">Copied</span>
    """
    st.markdown(html, unsafe_allow_html=True)

def groq_chat(history_messages):
    """Call Groq (or fallback echo)"""
    if client:
        try:
            resp = client.chat.completions.create(model=MODEL, messages=history_messages)
            return resp.choices[0].message.content
        except Exception as e:
            return f"⚠️ Error contacting model: {e}"
    # fallback (no Groq): simple echo style reply
    last_user = ""
    for m in reversed(history_messages):
        if m["role"] == "user":
            last_user = m["content"]
            break
    return f"(local) Mehnitavi echoing: {last_user[:400]}"

def extract_file_text(uploaded_file):
    """Try extract text from file or return a short descriptor."""
    if not uploaded_file:
        return None
    if PDF_AVAILABLE and uploaded_file.type == "application/pdf":
        try:
            reader = PdfReader(uploaded_file)
            pages = [p.extract_text() or "" for p in reader.pages]
            txt = "\n".join(pages).strip()
            return txt if txt else f"[PDF uploaded: {uploaded_file.name} — no text extracted]"
        except Exception:
            return f"[PDF uploaded: {uploaded_file.name} — extraction failed]"
    # text-like
    if uploaded_file.type.startswith("text/") or uploaded_file.name.lower().endswith(".txt"):
        try:
            return uploaded_file.read().decode("utf-8", errors="ignore")
        except Exception:
            return f"[Text file uploaded: {uploaded_file.name} — unreadable]"
    # images / audio / unknown -> descriptor
    return f"[File uploaded: {uploaded_file.name} — type: {uploaded_file.type or 'unknown'}]"

# ----------------- Session Store -----------------
store = st.session_state.setdefault("store", {"active": {}, "archived": {}})
current_id = st.session_state.setdefault("current_id", None)

# helpers to manage chats
def new_chat():
    cid = _uid()
    store["active"][cid] = {"title": "New Chat", "created_at": datetime.now().isoformat(), "messages": []}
    st.session_state.current_id = cid

def open_chat(cid):
    st.session_state.current_id = cid

def autotitle_if_needed(cid):
    chat = store["active"].get(cid)
    if not chat:
        return
    if chat["title"] == "New Chat":
        for m in chat["messages"]:
            if m["role"] == "user" and m["content"].strip():
                chat["title"] = m["content"].strip()[:40]
                break

# ----------------- Sidebar -----------------
with st.sidebar:
    st.header("Options")
    if st.button("✍️ New chat", use_container_width=True):
        new_chat()
        st.experimental_rerun()

    st.markdown("---")
    st.subheader("Chats")
    if not store["active"]:
        st.caption("No chats yet. Start one!")
    else:
        # newest first
        for cid, chat in list(store["active"].items())[::-1]:
            c1, c2 = st.columns([0.8, 0.2])
            if c1.button(chat["title"] or "Untitled", key=f"open_{cid}", use_container_width=True):
                open_chat(cid)
            with c2:
                with st.expander("⋮"):
                    new_name = st.text_input("Rename", value=chat["title"], key=f"rn_{cid}")
                    if st.button("Save name", key=f"save_name_{cid}"):
                        rename = new_name.strip()
                        if rename:
                            store["active"][cid]["title"] = rename

# ----------------- Main -----------------
st.title("🤖 Mehnitavi")

# create initial chat if none
if current_id is None:
    new_chat()

# show current chat UI
if current_id and current_id in store["active"]:
    chat = store["active"][current_id]

    # render messages
    for idx, msg in enumerate(chat["messages"]):
        role = msg["role"]
        with st.chat_message(role):
            st.markdown(msg["content"])

            # User messages: show Edit button (edit only user's messages)
            if role == "user":
                edit_key = f"edit_msg_{msg['id']}"
                if st.session_state.get(edit_key + "_active"):
                    # show textarea to edit and Save/Cancel
                    new_text = st.text_area("Edit your message", value=msg["content"], key=edit_key + "_area")
                    c1, c2 = st.columns([1,1])
                    with c1:
                        if st.button("Save", key=edit_key + "_save"):
                            chat["messages"][idx]["content"] = new_text
                            st.session_state.pop(edit_key + "_active", None)
                            st.experimental_rerun()
                    with c2:
                        if st.button("Cancel", key=edit_key + "_cancel"):
                            st.session_state.pop(edit_key + "_active", None)
                            st.experimental_rerun()
                else:
                    if st.button("✏️ Edit", key=edit_key + "_btn"):
                        st.session_state[edit_key + "_active"] = True
                        st.experimental_rerun()

            # Assistant messages: toolbar (copy, like, dislike, listen placeholder, share(download), regenerate)
            else:
                # copy
                render_copy_js(msg["content"], key=msg["id"])
                # like / dislike (simple feedback into session)
                col_like, col_dislike, col_listen, col_share, col_regen = st.columns([0.5,0.5,1,1,1])
                with col_like:
                    if st.button("👍", key=f"like_{msg['id']}"):
                        st.toast("Thanks for your feedback 👍")
                with col_dislike:
                    if st.button("👎", key=f"dislike_{msg['id']}"):
                        st.toast("Thanks — we'll try to improve 👎")
                with col_listen:
                    if st.button("🔊 Listen (download)", key=f"listen_{msg['id']}"):
                        # provide downloadable .txt as a simple listen placeholder (server-side TTS would be separate)
                        st.download_button("Download text", data=msg["content"], file_name=f"reply_{msg['id']}.txt")
                with col_share:
                    if st.button("📤 Share (download)", key=f"share_{msg['id']}"):
                        st.download_button("Download reply", data=msg["content"], file_name=f"reply_{msg['id']}.txt")
                with col_regen:
                    if st.button("🔄 Regenerate", key=f"regen_{msg['id']}"):
                        # Build history up to this assistant message
                        history = []
                        history.append({"role": "system", "content": "You are Mehnitavi, a helpful assistant."})
                        # include all messages before this assistant (to recreate context)
                        for h in chat["messages"][:idx]:
                            history.append({"role": h["role"], "content": h["content"]})
                        # call model (or fallback)
                        new_reply = groq_chat(history)
                        chat["messages"][idx]["content"] = new_reply
                        st.experimental_rerun()

    # ----------------- Inline upload + input -----------------
    c1, c2 = st.columns([0.08, 0.92])
    with c1:
        uploaded_file = st.file_uploader("", type=["png","jpg","jpeg","pdf","txt","mp3","wav"], label_visibility="collapsed")
    with c2:
        user_text = st.chat_input("Ask Mehnitavi something…")

    # If user uploaded a file (we attach as a user message)
    if uploaded_file:
        content = extract_file_text(uploaded_file)
        user_msg = {"id": _uid(), "role": "user", "content": content}
        chat["messages"].append(user_msg)
        # do not auto-call model here; let user press enter or you can call immediately:
        # here we will call model immediately to keep behavior consistent
        history = [{"role":"system","content":"You are Mehnitavi, a helpful assistant."}] + [
            {"role":m["role"], "content":m["content"]} for m in chat["messages"]
        ]
        assistant_reply = groq_chat(history)
        chat["messages"].append({"id": _uid(), "role":"assistant", "content": assistant_reply})
        autotitle_if_needed(current_id)
        st.experimental_rerun()

    # If user typed text
    if user_text:
        user_msg = {"id": _uid(), "role":"user", "content": user_text}
        chat["messages"].append(user_msg)

        # Prepare model history (system + all turns)
        history = [{"role":"system","content":"You are Mehnitavi, a helpful assistant."}] + [
            {"role":m["role"], "content":m["content"]} for m in chat["messages"]
        ]
        assistant_reply = groq_chat(history)
        chat["messages"].append({"id": _uid(), "role":"assistant", "content": assistant_reply})
        autotitle_if_needed(current_id)
        st.experimental_rerun()

else:
    st.info("Start a new chat from the sidebar.")
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
            if m["role"] == "assistant":
                cc1, cc2 = st.columns([0.15, 0.15])
                with cc1:
                    st.code(m["content"], language="markdown")
                with cc2:
                    new_text = st.text_area("✏️ Edit reply", m["content"], key=f"edit_{i}")
                    if st.button("💾 Save edit", key=f"save_{i}"):
                        chat["messages"][i]["content"] = new_text
                        st.rerun()

    # --- Input methods ---
    c1, c2 = st.columns([3, 1])

    with c1:
        text = st.chat_input("Ask Mehnitavi something…")

    with c2:
        uploaded_file = st.file_uploader(
            "📎",
            type=["png", "jpg", "jpeg", "pdf", "txt", "mp3", "wav"],
            label_visibility="collapsed"
        )

    # Handle text input
    if text:
        chat["messages"].append({"role": "user", "content": text})

    # Handle file input
    if uploaded_file:
        file_content = None
        if uploaded_file.type == "application/pdf":
            pdf_reader = PdfReader(uploaded_file)
            file_content = "\n".join([page.extract_text() for page in pdf_reader.pages if page.extract_text()])
        elif uploaded_file.type.startswith("text/"):
            file_content = uploaded_file.read().decode("utf-8")
        else:
            file_content = f"📎 Uploaded file: {uploaded_file.name}"

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

