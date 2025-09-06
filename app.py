import streamlit as st
import os
import json
from datetime import datetime
from groq import Groq
from PyPDF2 import PdfReader
from docx import Document
import pandas as pd

# -------------------
# Page Config
# -------------------
st.set_page_config(
    page_title="Mehnitavi",
    page_icon="🤖",
    layout="wide"
)

# -------------------
# Groq API Client
# -------------------
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
client = Groq(api_key=GROQ_API_KEY)

# -------------------
# Sidebar
# -------------------
st.sidebar.markdown("### ⚙️ Options")
st.sidebar.write("Mehnitavi AI Assistant")

# Theme Selector
theme = st.sidebar.radio("Theme", ["Light", "Dark"])

# Apply Dark Mode via CSS
if theme == "Dark":
    st.markdown(
        """
        <style>
        body, .stApp {
            background-color: #1e1e1e;
            color: white;
        }
        .stTextInput, .stTextArea, .stChatInput {
            background-color: #2b2b2b;
            color: white;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

# -------------------
# Session State Setup
# -------------------
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "👋 Hello — I’m Mehnitavi. Ask me anything or upload files for me to read."}
    ]
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
                if is_user:  # edit button only for user messages
                    if st.button("✏️ Edit", key=f"edit_btn_{i}"):
                        st.session_state.edit_mode[i] = True
                        st.rerun()

# -------------------
# Main App Layout
# -------------------
st.title("🤖 Mehnitavi - AI Chatbot")

# Render previous messages
render_messages()

# Chat input with file upload option
col1, col2 = st.columns([0.15, 0.85])
with col1:
    uploaded_file = st.file_uploader("", type=["pdf", "docx", "doc", "xlsx", "xls", "txt"], label_visibility="collapsed")
with col2:
    prompt = st.chat_input("Type your message...")

# -------------------
# Handle Uploaded File
# -------------------
if uploaded_file:
    file_text = process_file(uploaded_file)
    st.session_state.messages.append({"role": "user", "content": f"📄 Uploaded file: {uploaded_file.name}"})
    st.session_state.messages.append({"role": "assistant", "content": f"Here’s the extracted content:\n\n{file_text}"})
    st.rerun()

# -------------------
# Handle Text Input (Groq AI Integration)
# -------------------
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})

    try:
        completion = client.chat.completions.create(
            model="llama-3.1-70b-versatile",  # ✅ Updated model
            messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
        )
        reply = completion.choices[0].message["content"]
    except Exception as e:
        reply = f"❌ Error: {e}"

    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.rerun()
