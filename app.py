import streamlit as st
import os
from groq import Groq
import tempfile
from PyPDF2 import PdfReader
import pandas as pd
import docx

# -------------------------------
# Page config
# -------------------------------
st.set_page_config(page_title="Mehnitavi", page_icon="🤖", layout="wide")

# -------------------------------
# Sidebar branding
# -------------------------------
with st.sidebar:
    st.image("robot.png", width=100)  # Make sure robot.png is in your repo
    st.title("Mehnitavi")

# -------------------------------
# Groq client setup
# -------------------------------
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# -------------------------------
# Session state
# -------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = None

# -------------------------------
# Helper: read uploaded files
# -------------------------------
def read_file(uploaded_file):
    if uploaded_file is None:
        return None

    # PDFs
    if uploaded_file.type == "application/pdf":
        reader = PdfReader(uploaded_file)
        return "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])

    # Excel
    elif uploaded_file.type in [
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ]:
        df = pd.read_excel(uploaded_file)
        return df.to_string()

    # Word
    elif uploaded_file.type in [
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword",
    ]:
        doc = docx.Document(uploaded_file)
        return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])

    # Images (basic handling)
    elif uploaded_file.type.startswith("image/"):
        return f"[Image uploaded: {uploaded_file.name}]"

    # Text
    else:
        return uploaded_file.read().decode("utf-8", errors="ignore")

# -------------------------------
# Display chat history
# -------------------------------
for idx, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

        if msg["role"] == "user":
            if st.session_state.edit_mode == idx:
                new_text = st.text_area("✏️ Edit message:", msg["content"], key=f"edit_{idx}")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Save", key=f"save_{idx}"):
                        st.session_state.messages[idx]["content"] = new_text
                        st.session_state.edit_mode = None
                        st.rerun()
                with col2:
                    if st.button("❌ Cancel", key=f"cancel_{idx}"):
                        st.session_state.edit_mode = None
                        st.rerun()
            else:
                if st.button("✏️ Edit", key=f"edit_btn_{idx}"):
                    st.session_state.edit_mode = idx
                    st.rerun()

# -------------------------------
# Input area (chat + upload)
# -------------------------------
col1, col2 = st.columns([8, 1])

with col1:
    prompt = st.chat_input("Type your message here...")

with col2:
    uploaded_file = st.file_uploader("➕", type=["pdf", "docx", "doc", "xlsx", "xls", "txt", "png", "jpg", "jpeg"],
                                     label_visibility="collapsed")

if uploaded_file is not None:
    file_content = read_file(uploaded_file)
    if file_content:
        st.session_state.messages.append({"role": "user", "content": f"Uploaded file content:\n{file_content}"})
        with st.chat_message("user"):
            st.markdown(f"📂 Uploaded **{uploaded_file.name}**")

# -------------------------------
# Handle prompt
# -------------------------------
if prompt:
    # Save user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Call Groq API
    try:
        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
        )
        reply = response.choices[0].message.content

    except Exception as e:
        reply = f"⚠️ Error: {e}"

    # Save assistant reply
    st.session_state.messages.append({"role": "assistant", "content": reply})
    with st.chat_message("assistant"):
        st.markdown(reply)
