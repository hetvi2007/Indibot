# app.py
import streamlit as st
import uuid
import io
import os
from datetime import datetime

# optional imports (handled gracefully)
try:
    from PyPDF2 import PdfReader
    PDF_AVAILABLE = True
except Exception:
    PDF_AVAILABLE = False

try:
    from docx import Document
    DOCX_AVAILABLE = True
except Exception:
    DOCX_AVAILABLE = False

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except Exception:
    PANDAS_AVAILABLE = False

# -----------------------
# Page config & helper
# -----------------------
st.set_page_config(page_title="Mehnitavi", page_icon="🤖", layout="wide")
st.sidebar.markdown("### 🤖 Mehnitavi")
st.sidebar.write("A friendly rule-based knowledge assistant — tech + general knowledge")

def _uid():
    return uuid.uuid4().hex[:8]

# -----------------------
# Session state init
# -----------------------
if "chats" not in st.session_state:
    st.session_state.chats = []  # list of chat dicts
if "current" not in st.session_state:
    # create an initial chat
    st.session_state.current = 0
    st.session_state.chats.append({
        "id": _uid(),
        "title": "Chat 1",
        "created_at": datetime.now().isoformat(),
        "messages": [
            {"id": _uid(), "role": "assistant", "content": "👋 Hello — I’m Mehnitavi. Ask me anything about technology, science, history, or upload files for me to read."}
        ],
        "files": []  # store uploaded file metadata/content
    })
if "edit_buffer" not in st.session_state:
    st.session_state.edit_buffer = {}  # id -> draft text
if "last_topic" not in st.session_state:
    st.session_state.last_topic = None  # for follow-ups

# -----------------------
# Small knowledge base
# -----------------------
# This is where we expand rule-based knowledge. Extend as needed.
KB = {
    "programming languages": "There are hundreds of programming languages. Popular ones include Python, Java, C, C++, JavaScript. If you want, I can list them by domain (web, data, systems).",
    "python": "Python is a high-level language great for beginners and used widely in data science, web development, automation, and AI. Key libraries: numpy, pandas, scikit-learn, tensorflow.",
    "java": "Java is a versatile, compiled language commonly used for enterprise apps and Android development. It emphasizes portability via the JVM.",
    "c++": "C++ is a powerful systems language used for performance-critical applications, games, and native libraries.",
    "javascript": "JavaScript runs in browsers and on servers (Node.js). It's the main language for interactive web applications.",
    "operating system": "An operating system manages hardware and software resources. Examples: Windows, macOS, Linux. Ask me about any OS for details.",
    "history": "History covers events, dates, and people. Ask me about a specific era, country, or person and I’ll summarize key points.",
    "science": "Science is the systematic study of the physical and natural world. Tell me a field (physics, chemistry, biology) to get a focused summary.",
    "geography": "Geography studies places and relationships between people and their environments. Ask about countries, capitals, landscapes, or climate.",
    "hello": "Hi there! 👋 How can I help you today?"
}

# simple synonyms mapping
KB_KEYS = list(KB.keys())

def rule_based_response(text: str, context_topic=None):
    t = text.lower().strip()
    # direct matches first
    for key in KB_KEYS:
        if key in t:
            st.session_state.last_topic = key
            return KB[key]
    # follow-up using last_topic
    if context_topic:
        # if last topic exists and user asks follow-up like "tell me more" or "explain"
        if any(w in t for w in ["more", "explain", "detail", "tell me about", "what is", "why", "how"]):
            k = context_topic
            if k in KB:
                return KB[k] + "\n\n(If you'd like examples or code snippets, ask for them.)"
    # other heuristic answers
    if any(w in t for w in ["how many", "how many languages", "number of languages", "count of languages"]):
        st.session_state.last_topic = "programming languages"
        return KB["programming languages"]
    if any(greet in t for greet in ["hi", "hello", "hey"]):
        return KB["hello"]
    if "help" in t:
        return "I can answer questions about technology, science, history, geography, and I can extract content from uploaded files. Try: 'How many programming languages are there?' or 'Summarize the uploaded file.'"
    # fallback
    return "I’m not sure about that exact question. Try asking differently or upload a file and I can extract and analyze it."

# -----------------------
# File processing helpers
# -----------------------
def extract_pdf_text(uploaded_file):
    if not PDF_AVAILABLE:
        return "PDF support not installed (PyPDF2 missing)."
    try:
        reader = PdfReader(uploaded_file)
        pages = []
        for p in reader.pages:
            pages.append(p.extract_text() or "")
        return "\n".join(pages).strip()
    except Exception as e:
        return f"[PDF parse error: {e}]"

def extract_docx_text(uploaded_file):
    if not DOCX_AVAILABLE:
        return "DOCX support not installed (python-docx missing)."
    try:
        doc = Document(uploaded_file)
        return "\n".join([p.text for p in doc.paragraphs if p.text]).strip()
    except Exception as e:
        return f"[DOCX parse error: {e}]"

def extract_xls_text(uploaded_file):
    if not PANDAS_AVAILABLE:
        return "Excel support not installed (pandas missing)."
    try:
        df = pd.read_excel(uploaded_file)
        return df.to_string()
    except Exception as e:
        return f"[Excel parse error: {e}]"

def safe_read_text(uploaded_file):
    try:
        return uploaded_file.read().decode("utf-8", errors="ignore")
    except Exception:
        return "[Could not decode text file]"

# -----------------------
# UI: Chat area (left) and actions (right)
# -----------------------
st.title("🤖 Mehnitavi — Rule-based Knowledge Assistant")

col_main, col_actions = st.columns([3,1])
with col_actions:
    st.markdown("## Options")
    if st.button("➕ New Chat", use_container_width=True):
        st.session_state.chats.append({
            "id": _uid(),
            "title": f"Chat {len(st.session_state.chats)+1}",
            "created_at": datetime.now().isoformat(),
            "messages": [],
            "files": []
        })
        st.session_state.current = len(st.session_state.chats)-1
        st.experimental_rerun()
    st.markdown("---")
    st.write("Chats")
    for idx, c in enumerate(st.session_state.chats):
        if st.button(c["title"], key=f"open_{idx}", use_container_width=True):
            st.session_state.current = idx
            st.experimental_rerun()
    st.markdown("---")
    st.write("Tip: upload files next to the input box; Mehnitavi will read them and summarize.")

# current chat reference
chat = st.session_state.chats[st.session_state.current]

# render messages
def ensure_ids_and_render():
    for i, m in enumerate(chat["messages"]):
        if "id" not in m:
            m["id"] = _uid()
            chat["messages"][i] = m

    for i, m in enumerate(chat["messages"]):
        role = m.get("role", "assistant")
        with st.chat_message(role):
            if role == "user" and st.session_state.edit_buffer.get(m["id"]) is not None:
                # show editable textarea (persist in edit_buffer until save/cancel)
                new_text = st.text_area("Edit your message:", value=st.session_state.edit_buffer[m["id"]], key=f"edit_{m['id']}")
                c1, c2 = st.columns([1,1])
                with c1:
                    if st.button("Save", key=f"save_{m['id']}"):
                        # find index again (ids stable)
                        for j, mm in enumerate(chat["messages"]):
                            if mm.get("id")==m["id"]:
                                chat["messages"][j]["content"] = new_text
                                break
                        st.session_state.edit_buffer.pop(m["id"], None)
                        st.experimental_rerun()
                with c2:
                    if st.button("Cancel", key=f"cancel_{m['id']}"):
                        st.session_state.edit_buffer.pop(m["id"], None)
                        st.experimental_rerun()
            else:
                # show content (images treated specially if stored)
                if m.get("type") == "image":
                    try:
                        st.image(m["content"], caption=m.get("filename","image"), use_column_width=True)
                    except Exception:
                        st.write(f"[Image: {m.get('filename','unknown')}]")
                else:
                    st.markdown(m.get("content",""))
                # user controls
                if role == "user":
                    c1, c2 = st.columns([0.5,0.5])
                    with c1:
                        if st.button("✏️ Edit", key=f"editbtn_{m['id']}"):
                            st.session_state.edit_buffer[m["id"]] = m["content"]
                            st.experimental_rerun()
                    with c2:
                        if st.button("📋 Copy", key=f"copy_{m['id']}"):
                            st.code(m["content"])
                            st.toast("Copied (select & Ctrl+C)")

ensure_ids_and_render()

# input area: file uploader inline + chat input
input_col, upload_col = st.columns([0.85, 0.15])
with upload_col:
    uploaded_files = st.file_uploader("", accept_multiple_files=True, type=None, label_visibility="collapsed")
with input_col:
    user_text = st.chat_input("Ask Mehnitavi something or press Enter to send...")

# Handle uploaded files (if any)
if uploaded_files:
    for uf in uploaded_files:
        fname = uf.name
        fext = fname.split(".")[-1].lower()
        extracted = ""
        msg_type = "text"
        if fext == "pdf":
            extracted = extract_pdf_text(uf) if PDF_AVAILABLE else "PDF support not installed."
        elif fext in ("docx","doc"):
            extracted = extract_docx_text(uf) if DOCX_AVAILABLE else "DOCX support not installed."
        elif fext in ("xls","xlsx"):
            extracted = extract_xls_text(uf) if PANDAS_AVAILABLE else "Excel support not installed."
        elif fext in ("txt","csv","md","json","log"):
            extracted = safe_read_text(uf)
        elif uf.type and uf.type.startswith("image/"):
            # keep binary content for preview
            try:
                raw = uf.getvalue()
                msg_type = "image"
                extracted = raw  # store bytes for st.image
            except Exception:
                extracted = f"[Image file: {fname}]"
        else:
            extracted = f"[File uploaded: {fname} — unsupported for text extraction]"

        # store file metadata in chat
        chat["files"].append({"filename": fname, "type": fext, "extracted_preview": str(extracted)[:1000]})

        # add messages: user upload + assistant extracted content
        if msg_type == "image":
            chat["messages"].append({"id": _uid(), "role":"user", "content": f"📷 Uploaded image: {fname}", "type":"text"})
            chat["messages"].append({"id": _uid(), "role":"user", "content": extracted, "type":"image", "filename": fname})
        else:
            preview_text = extracted if isinstance(extracted, str) else str(extracted)
            chat["messages"].append({"id": _uid(), "role":"user", "content": f"📄 Uploaded file: {fname}", "type":"text"})
            chat["messages"].append({"id": _uid(), "role":"assistant", "content": f"Here is the extracted content from **{fname}**:\n\n{preview_text[:3000]}", "type":"text"})
    st.experimental_rerun()

# Handle typed user input
if user_text:
    # append user message
    user_msg = {"id": _uid(), "role":"user", "content": user_text}
    chat["messages"].append(user_msg)

    # produce rule-based reply (use context last_topic if set)
    reply = rule_based_response(user_text, context_topic=st.session_state.last_topic)
    # if the user asks to "summarize uploaded file" handle that
    if any(kw in user_text.lower() for kw in ["summarize", "summary", "summarise", "short"]):
        # prefer latest file in chat
        if chat["files"]:
            last_file = chat["files"][-1]
            reply = f"I can summarize **{last_file['filename']}**. Preview:\n\n{last_file['extracted_preview'][:2000]}\n\nAsk 'Summarize this file' to get a concise summary (I will compress main points)."
        else:
            reply = "You didn't upload a file yet. Upload a file (PDF/DOCX/XLSX/TXT or image) using the + button and I'll extract and summarize it."

    # add assistant response
    chat["messages"].append({"id": _uid(), "role":"assistant", "content": reply})
    st.experimental_rerun()
