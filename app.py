import streamlit as st
from groq import Groq
import uuid
from PyPDF2 import PdfReader
from docx import Document
import pandas as pd
from pptx import Presentation

# --- Groq API Client ---
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# --- Generate unique IDs for messages ---
def _uid():
    return str(uuid.uuid4())[:8]

# --- Initialize session state ---
if "chats" not in st.session_state:
    st.session_state.chats = [{"title": "New Chat", "messages": []}]
if "current_chat" not in st.session_state:
    st.session_state.current_chat = 0

chats = st.session_state.chats
chat = chats[st.session_state.current_chat]

# --- Sidebar (chat list) ---
st.sidebar.title("💬 Mehnitavi")
for i, c in enumerate(chats):
    if st.sidebar.button(c["title"], key=f"chat_{i}"):
        st.session_state.current_chat = i
        st.rerun()
if st.sidebar.button("➕ New Chat"):
    chats.append({"title": "New Chat", "messages": []})
    st.session_state.current_chat = len(chats) - 1
    st.rerun()

# --- Chat Display ---
st.title("🤖 Mehnitavi")

for msg in chat["messages"]:
    with st.chat_message("user" if msg["role"] == "user" else "assistant"):
        if msg.get("type") == "image":
            st.image(msg["content"], caption=msg.get("filename", "Uploaded image"))
        else:
            st.markdown(msg["content"])
        if msg["role"] == "user":  # ✅ Only user's messages editable
            if st.button("✏️ Edit", key=f"edit_{msg['id']}"):
                new_text = st.text_area("Edit message:", value=msg["content"], key=f"edit_text_{msg['id']}")
                if st.button("Save", key=f"save_{msg['id']}"):
                    msg["content"] = new_text
                    st.rerun()

# --- Input + File Upload Row ---
col1, col2 = st.columns([8, 1])
with col1:
    user_input = st.chat_input("Type your message...")
with col2:
    uploaded_files = st.file_uploader("➕", type=None, accept_multiple_files=True, label_visibility="collapsed")

# --- Handle text input ---
if user_input:
    chat["messages"].append({"role": "user", "content": user_input, "id": _uid(), "type": "text"})

    try:
        completion = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": m["role"], "content": m["content"]} for m in chat["messages"] if m["type"] == "text"]
        )
        bot_reply = completion.choices[0].message.content
    except Exception as e:
        bot_reply = f"⚠️ Error: {str(e)}"

    chat["messages"].append({"role": "assistant", "content": bot_reply, "id": _uid(), "type": "text"})
    st.rerun()

# --- Handle file uploads ---
if uploaded_files:
    for uploaded_file in uploaded_files:
        content = ""
        msg_type = "text"

        # PDFs
        if uploaded_file.type == "application/pdf":
            reader = PdfReader(uploaded_file)
            content = "\n".join([page.extract_text() or "" for page in reader.pages])

        # Word
        elif uploaded_file.type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                    "application/msword"]:
            doc = Document(uploaded_file)
            content = "\n".join([p.text for p in doc.paragraphs])

        # Excel
        elif uploaded_file.type in ["application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                    "application/vnd.ms-excel"]:
            df = pd.read_excel(uploaded_file)
            content = df.to_string()

        # PowerPoint
        elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.presentationml.presentation":
            prs = Presentation(uploaded_file)
            slides = []
            for slide in prs.slides:
                texts = []
                for shape in slide.shapes:
                    if hasattr(shape, "text"):
                        texts.append(shape.text)
                slides.append("\n".join(texts))
            content = "\n\n".join(slides)

        # Text, CSV, JSON, MD, logs
        elif uploaded_file.type.startswith("text/") or uploaded_file.name.endswith((".txt", ".csv", ".json", ".log", ".md")):
            content = uploaded_file.read().decode("utf-8")

        # Images
        elif uploaded_file.type.startswith("image/"):
            content = uploaded_file
            msg_type = "image"

        # Other files
        else:
            content = f"📎 Uploaded file: {uploaded_file.name} ({uploaded_file.size/1024:.1f} KB)"

        chat["messages"].append({
            "role": "user",
            "content": content,
            "id": _uid(),
            "type": msg_type,
            "filename": uploaded_file.name
        })

    st.rerun()
