import streamlit as st
from PyPDF2 import PdfReader
from docx import Document
import pandas as pd
import os

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
# Session State Setup
# -------------------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = {}

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
    for i, msg in enumerate(st.session_state.messages):
        is_user = msg["role"] == "user"
        with st.chat_message("user" if is_user else "assistant"):
            if st.session_state.edit_mode.get(i, False) and is_user:
                new_text = st.text_area("Edit your message:", msg["content"], key=f"edit_box_{i}")
                if st.button("Save", key=f"save_btn_{i}"):
                    st.session_state.messages[i]["content"] = new_text
                    st.session_state.edit_mode[i] = False
                    st.rerun()
                if st.button("Cancel", key=f"cancel_btn_{i}"):
                    st.session_state.edit_mode[i] = False
                    st.rerun()
            else:
                st.markdown(msg["content"])
                if is_user:  # ✅ edit button only for user messages
                    if st.button("✏️ Edit", key=f"edit_btn_{i}"):
                        st.session_state.edit_mode[i] = True
                        st.rerun()

# -------------------
# Main App Layout
# -------------------
st.title("🤖 Mehnitavi - AI Chatbot")

# File Upload (via + button in chat input area)
uploaded_file = st.file_uploader("➕ Upload a file (PDF, DOCX, XLSX, TXT)", type=["pdf", "docx", "doc", "xlsx", "xls", "txt"])

if uploaded_file:
    file_text = process_file(uploaded_file)
    st.session_state.messages.append({"role": "user", "content": f"📄 Uploaded file: {uploaded_file.name}"})
    st.session_state.messages.append({"role": "assistant", "content": f"Here’s the extracted content:\n\n{text}"})

# Render previous messages
render_messages()

# Chat input
if prompt := st.chat_input("Type your message..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Dummy bot response
    st.session_state.messages.append({"role": "assistant", "content": f"You said: {prompt}"})
    st.rerun()
