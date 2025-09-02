import streamlit as st
import pandas as pd
import PyPDF2
from docx import Document
from groq import Groq
from PIL import Image
import io

# -------------------
# Page Config
# -------------------
st.set_page_config(page_title="Mehnitavi", page_icon="🤖", layout="wide")

# Initialize Groq client
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# -------------------
# Sidebar
# -------------------
st.sidebar.image("robot.png", width=100)
st.sidebar.title("Mehnitavi 🤖")
st.sidebar.write("Your AI Assistant")

# -------------------
# Session State
# -------------------
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# -------------------
# Helper: Read uploaded files
# -------------------
def read_file(uploaded_file):
    if uploaded_file.type == "application/pdf":
        reader = PyPDF2.PdfReader(uploaded_file)
        return "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
    
    elif uploaded_file.type in [
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword",
    ]:
        doc = Document(uploaded_file)
        return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
    
    elif uploaded_file.type in [
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-excel",
    ]:
        df = pd.read_excel(uploaded_file)
        return df.to_string()
    
    elif uploaded_file.type.startswith("image/"):
        image = Image.open(uploaded_file)
        buf = io.BytesIO()
        image.save(buf, format="PNG")
        return "📷 Image uploaded successfully (content not extracted as text)."
    
    else:
        return uploaded_file.read().decode("utf-8", errors="ignore")

# -------------------
# Chat UI
# -------------------
st.title("💬 Mehnitavi")

# Show past messages
for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Input area
user_input = st.chat_input("Type your message here...")

# File uploader button
uploaded_file = st.file_uploader("➕ Upload a file", type=None, label_visibility="collapsed")

if uploaded_file:
    file_text = read_file(uploaded_file)
    st.session_state["messages"].append({"role": "user", "content": f"📎 Uploaded file:\n{file_text}"})
    with st.chat_message("user"):
        st.markdown(f"📎 Uploaded file:\n{file_text}")

# Handle chat input
if user_input:
    st.session_state["messages"].append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        try:
            response = client.chat.completions.create(
                model="llama3-8b-8192",
                messages=st.session_state["messages"],
                stream=True,
            )
            for chunk in response:
                delta = chunk.choices[0].delta.content or ""
                full_response += delta
                message_placeholder.markdown(full_response + "▌")
        except Exception as e:
            full_response = f"⚠️ Error: {str(e)}"

        message_placeholder.markdown(full_response)
    st.session_state["messages"].append({"role": "assistant", "content": full_response})
