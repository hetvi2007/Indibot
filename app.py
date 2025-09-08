import streamlit as st
from PyPDF2 import PdfReader
from docx import Document
import pandas as pd
from PIL import Image
import io
import json
from datetime import datetime

# -------------------
# Page Config
# -------------------
st.set_page_config(page_title="🤖 Smart Chatbot", layout="wide")

# -------------------
# Theme (Dark/Light)
# -------------------
if "theme" not in st.session_state:
    st.session_state.theme = "Light"

theme_choice = st.sidebar.radio("🌗 Theme", ["Light", "Dark"])
st.session_state.theme = theme_choice

if theme_choice == "Dark":
    st.markdown(
        """
        <style>
        body, .stApp {
            background-color: #1E1E1E;
            color: white !important;
        }
        .stMarkdown, .stTextInput, .stChatMessage {
            color: white !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

# -------------------
# Session State Setup
# -------------------
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "👋 Hello — I’m Smart Chatbot. Ask me anything or upload a file to summarize."}
    ]

# -------------------
# File Processing
# -------------------
def process_file(uploaded_file):
    """Extract and summarize text from PDF, Word, Excel, or TXT files."""
    text = ""
    file_type = uploaded_file.name.split(".")[-1].lower()

    if file_type == "pdf":
        pdf_reader = PdfReader(uploaded_file)
        for page in pdf_reader.pages[:3]:
            text += page.extract_text() or ""
    elif file_type in ["docx", "doc"]:
        doc = Document(uploaded_file)
        for para in doc.paragraphs[:20]:
            text += para.text + "\n"
    elif file_type in ["xls", "xlsx"]:
        df = pd.read_excel(uploaded_file)
        text = df.head(10).to_string()
    elif file_type == "txt":
        text = uploaded_file.read().decode("utf-8")[:1000]
    else:
        text = f"⚠️ Unsupported file type: {file_type}"

    if len(text) > 800:
        text = text[:800] + "... (summary truncated)"
    return text

# -------------------
# Chat Rendering
# -------------------
def render_messages(messages):
    for msg in messages:
        with st.chat_message("user" if msg["role"] == "user" else "assistant"):
            st.markdown(msg["content"])

# -------------------
# Main App Layout
# -------------------
st.title("🤖 Smart Chatbot")

# Sidebar
st.sidebar.title("⚙️ Options")

# New Chat
if st.sidebar.button("🗑️ New Chat"):
    st.session_state.messages = [
        {"role": "assistant", "content": "👋 New chat started. What’s up?"}
    ]
    st.rerun()

# Download
if st.sidebar.button("💾 Download Chat History"):
    filename = f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    st.sidebar.download_button(
        "Download",
        data=json.dumps(st.session_state.messages, indent=2),
        file_name=filename,
        mime="application/json",
    )

# 🔍 Search chats
search_query = st.sidebar.text_input("🔍 Search chat history")
if search_query:
    filtered = [m for m in st.session_state.messages if search_query.lower() in m["content"].lower()]
    st.sidebar.markdown("### Results:")
    for f in filtered:
        st.sidebar.write(f"- **{f['role'].capitalize()}**: {f['content'][:50]}...")

# -------------------
# Display Messages
# -------------------
render_messages(st.session_state.messages)

# -------------------
# Input Section
# -------------------
col1, col2 = st.columns([0.2, 0.8])
with col1:
    uploaded_file = st.file_uploader("📂", type=["pdf", "docx", "doc", "xlsx", "xls", "txt"], label_visibility="collapsed")
with col2:
    prompt = st.chat_input("Type your message...")

# -------------------
# Handle File Upload
# -------------------
if uploaded_file:
    file_text = process_file(uploaded_file)
    st.session_state.messages.append({"role": "user", "content": f"📄 Uploaded: {uploaded_file.name}"})
    st.session_state.messages.append({"role": "assistant", "content": f"📑 File Summary:\n\n{file_text}"})
    st.rerun()

# -------------------
# Handle Chat Input
# -------------------
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})

    knowledge_base = {
        "python": "🐍 Python is great for AI, data science, and web apps.",
        "java": "☕ Java is widely used in enterprise software and Android apps.",
        "history": "📜 History tells us about past civilizations and events.",
        "science": "🔬 Science helps us explore and understand the world.",
        "ai": "🤖 AI means machines can think and learn like humans."
    }

    reply = None
    for keyword, answer in knowledge_base.items():
        if keyword in prompt.lower():
            reply = answer
            break

    if not reply:
        if "hello" in prompt.lower() or "hi" in prompt.lower():
            reply = "👋 Hi there! How can I help you?"
        else:
            reply = f"🤔 I don’t know that yet, but I can learn! You asked: {prompt}"

    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.rerun()

# -------------------
# Image Generator
# -------------------
st.subheader("🎨 Image Generator")
img_prompt = st.text_input("Describe an image:")
if st.button("Generate Image") and img_prompt:
    img = Image.new("RGB", (400, 400), color=(150, 100, 200))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    st.image(buf, caption=f"Generated: {img_prompt}", use_column_width=True)
