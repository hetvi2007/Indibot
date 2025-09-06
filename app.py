import streamlit as st
from PyPDF2 import PdfReader
from docx import Document
import pandas as pd
from groq import Groq
import os

# -------------------
# Page Config
# -------------------
st.set_page_config(
    page_title="Mehnitavi - AI Chatbot",
    page_icon="🤖",
    layout="wide"
)

# -------------------
# Setup Groq Client
# -------------------
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY") or os.environ.get("GROQ_API_KEY")

if not GROQ_API_KEY:
    st.error("❌ Missing API key. Please set `GROQ_API_KEY` in your `.streamlit/secrets.toml` or environment.")
    st.stop()

client = Groq(api_key=GROQ_API_KEY)

# -------------------
# Sidebar
# -------------------
st.sidebar.markdown("### ⚙️ Options")
st.sidebar.write("🤖 Mehnitavi AI Assistant")
theme = st.sidebar.radio("Theme", ["Light", "Dark"])

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

    try:
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
    except Exception as e:
        text = f"❌ Error reading file: {e}"

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
                if is_user:
                    if st.button("✏️ Edit", key=f"edit_btn_{i}"):
                        st.session_state.edit_mode[i] = True
                        st.rerun()

# -------------------
# Main App Layout
# -------------------
st.title("🤖 Mehnitavi - AI Chatbot")

# Render previous messages
render_messages()

# Input row (ChatGPT style: file upload + text input)
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
# Handle Text Input with Groq AI
# -------------------
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})

    try:
        completion = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {"role": "system", "content": "You are Mehnitavi, a helpful AI assistant."}
            ] + [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
        )
        reply = completion.choices[0].message["content"]
    except Exception as e:
        reply = f"❌ Error: {e}"

    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.rerun()
