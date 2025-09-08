import streamlit as st
import datetime

# ---------------- Session State Setup ----------------
if "chats" not in st.session_state:
    st.session_state.chats = {}
if "active_chat" not in st.session_state:
    st.session_state.active_chat = None
if "chat_counter" not in st.session_state:
    st.session_state.chat_counter = 0

# ---------------- Knowledge Brain ----------------
knowledge_base = {
    "what is your name": "I am Mehnitavi — your personal AI chatbot 🤖.",
    "how many languages in computer": "There are two main types: low-level (machine & assembly) and high-level (like Python, C, Java, etc.).",
    "different language used in india": "India has 22 official languages, including Hindi, English, Bengali, Tamil, Telugu, Kannada, Marathi, and more.",
    "what is computer": "A computer is an electronic device that processes information and performs tasks using hardware and software.",
    "who is father of computer": "Charles Babbage is called the Father of Computers.",
    "what is ai": "AI (Artificial Intelligence) is the simulation of human intelligence in machines that can think and learn."
}

def chatbot_reply(user_input: str):
    user_input = user_input.lower().strip()
    for key, answer in knowledge_base.items():
        if key in user_input:
            return answer
    return f"🤔 I don’t know this yet, but I can learn! You asked: {user_input}"

# ---------------- Chat Functions ----------------
def create_new_chat():
    st.session_state.chat_counter += 1
    chat_id = f"chat_{st.session_state.chat_counter}"
    st.session_state.chats[chat_id] = {
        "title": f"Chat {st.session_state.chat_counter}",
        "messages": [],
        "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    st.session_state.active_chat = chat_id

def add_message(role, content):
    if st.session_state.active_chat:
        st.session_state.chats[st.session_state.active_chat]["messages"].append(
            {"role": role, "content": content}
        )

# ---------------- Sidebar ----------------
st.sidebar.title("💬 Chat Manager")

if st.sidebar.button("➕ New Chat"):
    create_new_chat()

if st.session_state.chats:
    for chat_id, chat in st.session_state.chats.items():
        if st.sidebar.button(chat["title"], key=chat_id):
            st.session_state.active_chat = chat_id

# ---------------- Main Chat Area ----------------
st.title("🤖 Mehnitavi - AI Chatbot")
st.write("👋 Hello — I’m Mehnitavi. Ask me anything about technology, science, history, or upload files for me to read.")

# Auto-create first chat if none exists
if not st.session_state.active_chat:
    create_new_chat()

chat = st.session_state.chats[st.session_state.active_chat]

# Show chat history
for msg in chat["messages"]:
    with st.chat_message("user" if msg["role"] == "user" else "assistant"):
        st.markdown(msg["content"])

# ---------------- Chat Input (GPT-style) ----------------
user_input = st.chat_input("Type your message here...")

if user_input:
    add_message("user", user_input)
    bot_reply = chatbot_reply(user_input)
    add_message("assistant", bot_reply)
    st.experimental_rerun()

# ---------------- File Upload ----------------
st.subheader("📂 Upload a file")
uploaded_file = st.file_uploader("Upload TXT, PDF, or DOCX", type=["txt", "pdf", "docx"])
if uploaded_file:
    st.success(f"✅ File {uploaded_file.name} uploaded successfully!")
