import streamlit as st
from PyPDF2 import PdfReader
import pyperclip
from gtts import gTTS
import base64
import os

# ------------------------- Roll number to project topic -------------------------
def get_project_topic(roll_number):
    topics = {
        33: "AI-powered chatbot",
        34: "Blockchain-based voting system",
        35: "IoT smart home automation"
    }
    return topics.get(roll_number, "No topic assigned for this roll number")

# ------------------------- Helper functions -------------------------
def copy_to_clipboard(text):
    try:
        pyperclip.copy(text)
        st.toast("✅ Copied to clipboard")
    except Exception:
        st.warning("⚠️ Copy not supported in this environment")

def download_audio(text, key):
    """Generate an audio download link for text using gTTS"""
    tts = gTTS(text=text, lang="en")
    filename = f"tts_{key}.mp3"
    tts.save(filename)
    with open(filename, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    os.remove(filename)
    return f'<a href="data:audio/mp3;base64,{b64}" download="reply.mp3">▶️ Listen</a>'

# ------------------------- File processing -------------------------
def extract_text_from_file(uploaded_file):
    if uploaded_file.type == "application/pdf":
        pdf_reader = PdfReader(uploaded_file)
        return " ".join([page.extract_text() for page in pdf_reader.pages if page.extract_text()])
    elif uploaded_file.type.startswith("text/"):
        return uploaded_file.read().decode("utf-8")
    else:
        return "❌ Unsupported file type"

# ------------------------- Session state -------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "pending_edit" not in st.session_state:
    st.session_state.pending_edit = None

# ------------------------- Sidebar -------------------------
st.sidebar.header("📂 Upload File")
uploaded_file = st.sidebar.file_uploader("Upload PDF or TXT", type=["pdf", "txt"])
if uploaded_file:
    file_text = extract_text_from_file(uploaded_file)
    st.sidebar.success("✅ File uploaded and processed")

st.sidebar.header("🎓 Roll Number → Topic")
roll_number = st.sidebar.number_input("Enter roll number", min_value=1, step=1)
if st.sidebar.button("Get Topic"):
    topic = get_project_topic(roll_number)
    st.sidebar.write(f"**Project Topic:** {topic}")

# ------------------------- Main Chat -------------------------
st.title("🤖 Mehnitavi")

for idx, msg in enumerate(st.session_state.messages):
    role = "user" if msg["role"] == "user" else "assistant"
    bubble_class = f"bubble {role}"

    with st.container():
        st.markdown(f'<div class="{bubble_class}">', unsafe_allow_html=True)

        # Show message text
        st.markdown(msg["content"])

        # Assistant toolbar
        if msg["role"] == "assistant":
            col1, col2, col3, col4, col5, col6 = st.columns([1,1,1,1,1,1])

            with col1:
                if st.button("📋", key=f"copy-{idx}", help="Copy"):
                    copy_to_clipboard(msg["content"])

            with col2:
                if st.button("👍", key=f"like-{idx}", help="Like"):
                    st.toast("You liked this response")

            with col3:
                if st.button("👎", key=f"dislike-{idx}", help="Dislike"):
                    st.toast("You disliked this response")

            with col4:
                audio_html = download_audio(msg["content"], idx)
                st.markdown(audio_html, unsafe_allow_html=True)

            with col5:
                if st.button("📤", key=f"share-{idx}", help="Share"):
                    st.toast("Share option clicked")

            with col6:
                if st.button("🔄", key=f"regen-{idx}", help="Regenerate"):
                    # Re-run assistant on last user query
                    last_user_query = None
                    for m in reversed(st.session_state.messages[:idx]):
                        if m["role"] == "user":
                            last_user_query = m["content"]
                            break
                    if last_user_query:
                        st.session_state.messages.append(
                            {"role": "assistant", "content": f"🔄 Regenerated response for: {last_user_query}"}
                        )
                        st.rerun()

        else:
            # User message edit logic
            if st.session_state.pending_edit == msg.get("id"):
                new_text = st.text_area("Edit message", value=msg["content"], key=f"edit-{msg['id']}")
                col_e1, col_e2 = st.columns(2)
                with col_e1:
                    if st.button("Save", key=f"save-{msg['id']}"):
                        msg["content"] = new_text
                        st.session_state.pending_edit = None
                        st.rerun()
                with col_e2:
                    if st.button("Cancel", key=f"cancel-{msg['id']}"):
                        st.session_state.pending_edit = None
                        st.rerun()
            else:
                if st.button("✏️ Edit", key=f"editbtn-{idx}"):
                    st.session_state.pending_edit = msg.get("id", idx)
                    st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

# ------------------------- Chat Input -------------------------
user_input = st.chat_input("Ask Mehnitavi something...")
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    # Fake assistant response (replace with your LLM)
    st.session_state.messages.append({"role": "assistant", "content": f"Echo: {user_input}"})
    st.rerun()
