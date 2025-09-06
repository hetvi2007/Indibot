import streamlit as st
from PyPDF2 import PdfReader
from docx import Document
import pandas as pd
import uuid
from datetime import datetime

# -------------------
# Page Config
# -------------------
st.set_page_config(
    page_title="Mehnitavi",
    page_icon="🤖",
    layout="wide"
)

# -------------------
# Sidebar
# -------------------
st.sidebar.markdown("### 🤖 Mehnitavi")
st.sidebar.write("Your AI Assistant")

# -------------------
# Utilities
# -------------------
def _uid():
    """Generate unique id"""
    return str(uuid.uuid4())[:8]

# -------------------
# Session State Setup
# -------------------
if "chats" not in st.session_state:
    st.session_state.chats = [{
        "id": _uid(),
        "title": "New Chat",
        "created_at": datetime.now().isoformat(),
        "messages": [],
        "files": []
    }]
    st.session_state.current = 0
if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = {}
if "edit_buffer" not in st.session_state:
    st.session_state.edit_buffer = {}

# -------------------
# File Processing
# -------------------
def process_file(uploaded_file):
    """Extract text from PDF, Word, Excel, or TXT files."""
    text = ""
    file_type = uploaded_file.name.split(".")[-1].lower()

    if file_type == "pdf":
        pdf_reader = PdfReader(uploaded_file)
        for page in pdf_reader.pages:
            text += page.extract_text() or ""
    elif file_type in ["docx", "doc"]:
        doc = Document(uploaded_file)
        for para in doc.paragraphs:
            text += para.text + "\n"
    elif file_type in ["xls", "xlsx"]:
        df = pd.read_excel(uploaded_file)
        text = df.to_string()
    elif file_type == "txt":
        text = uploaded_file.read().decode("utf-8")
    else:
        text = f"⚠️ Unsupported file type: {file_type}"

    return text

# -------------------
# Chat Rendering
# -------------------
def render_messages():
    chat = st.session_state.chats[st.session_state.current]
    for i, msg in enumerate(chat["messages"]):
        is_user = msg["role"] == "user"
        with st.chat_message("user" if is_user else "assistant"):
            if st.session_state.edit_mode.get(msg["id"], False) and is_user:
                new_text = st.text_area(
                    "Edit your message:",
                    st.session_state.edit_buffer.get(msg["id"], msg["content"]),
                    key=f"edit_box_{msg['id']}"
                )
                if st.button("Save", key=f"save_btn_{msg['id']}"):
                    msg["content"] = new_text
                    st.session_state.edit_mode[msg["id"]] = False
                    st.session_state.edit_buffer.pop(msg["id"], None)
                    st.rerun()   # ✅ fixed
                if st.button("Cancel", key=f"cancel_btn_{msg['id']}"):
                    st.session_state.edit_mode[msg["id"]] = False
                    st.session_state.edit_buffer.pop(msg["id"], None)
                    st.rerun()   # ✅ fixed
            else:
                st.markdown(msg["content"])
                if is_user:  # edit button only for user messages
                    if st.button("✏️ Edit", key=f"edit_btn_{msg['id']}"):
                        st.session_state.edit_mode[msg["id"]] = True
                        st.session_state.edit_buffer[msg["id"]] = msg["content"]
                        st.rerun()   # ✅ fixed

# -------------------
# Main App Layout
# -------------------
st.title("🤖 Mehnitavi - AI Chatbot")

# Sidebar chat list
with st.sidebar:
    st.markdown("### 💬 Chats")
    if st.button("➕ New Chat", use_container_width=True):
        st.session_state.chats.append({
            "id": _uid(),
            "title": f"Chat {len(st.session_state.chats)+1}",
            "created_at": datetime.now().isoformat(),
            "messages": [],
            "files": []
        })
        st.session_state.current = len(st.session_state.chats)-1
        st.rerun()   # ✅ fixed

    for idx, c in enumerate(st.session_state.chats):
        if st.button(c["title"], key=f"open_{idx}", use_container_width=True):
            st.session_state.current = idx
            st.rerun()   # ✅ fixed

# Render previous messages
render_messages()

# Chat input with file upload option (like ChatGPT style)
col1, col2 = st.columns([0.15, 0.85])
with col1:
    uploaded_file = st.file_uploader(
        "",
        type=["pdf", "docx", "doc", "xlsx", "xls", "txt"],
        label_visibility="collapsed"
    )
with col2:
    prompt = st.chat_input("Type your message...")

# -------------------
# Handle Uploaded File
# -------------------
if uploaded_file:
    chat = st.session_state.chats[st.session_state.current]
    file_text = process_file(uploaded_file)
    chat["messages"].append({"id": _uid(), "role": "user", "content": f"📄 Uploaded file: {uploaded_file.name}"})
    chat["messages"].append({"id": _uid(), "role": "assistant", "content": f"Here’s the extracted content:\n\n{file_text}"})
    st.rerun()   # ✅ fixed

# -------------------
# Handle Text Input
# -------------------
if prompt:
    chat = st.session_state.chats[st.session_state.current]
    chat["messages"].append({"id": _uid(), "role": "user", "content": prompt})

    # Dummy rule-based brain (expandable later)
    if "language" in prompt.lower():
        reply = "💡 Computers support hundreds of programming languages like Python, Java, C++, etc. Would you like me to list some?"
    elif "hello" in prompt.lower() or "hi" in prompt.lower():
        reply = "👋 Hi! How can I help you today?"
    else:
        reply = f"You said: {prompt}"

    chat["messages"].append({"id": _uid(), "role": "assistant", "content": reply})
    st.rerun()   # ✅ fixed
