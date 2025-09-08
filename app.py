import streamlit as st
import openai

# --- Streamlit page config ---
st.set_page_config(page_title="Smart Chatbot", page_icon="🤖", layout="centered")

# --- Styling ---
st.markdown("""
    <style>
    .stChatMessage {
        background-color: #f0f2f6;
        padding: 12px 16px;
        border-radius: 12px;
        margin-bottom: 10px;
        max-width: 85%;
    }
    .user-message {
        background-color: #DCF8C6;
        margin-left: auto;
        text-align: right;
    }
    .ai-message {
        background-color: #F1F0F0;
        margin-right: auto;
        text-align: left;
    }
    .chat-container {
        height: 400px;
        overflow-y: auto;
        padding: 10px;
        border: 1px solid #ccc;
        border-radius: 10px;
        margin-bottom: 15px;
        background-color: #fff;
    }
    </style>
""", unsafe_allow_html=True)

# --- Title ---
st.title("🤖 Smart Chatbot")
st.subheader("Talk to an intelligent assistant that responds with purpose.")

# --- Initialize session state ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- OpenAI Setup ---
openai.api_key = st.secrets["OPENAI_API_KEY"]  # Securely stored in Streamlit Cloud

def get_gpt_response(prompt):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # or "gpt-4" if available
            messages=[
                {"role": "system", "content": "You are a smart and helpful assistant."},
                *st.session_state.messages,
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"⚠️ Error: {str(e)}"

# --- Chat Display ---
chat_container = st.container()
with chat_container:
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    for msg in st.session_state.messages:
        class_name = "user-message" if msg["role"] == "user" else "ai-message"
        st.markdown(f'<div class="stChatMessage {class_name}">{msg["content"]}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- User Input ---
user_input = st.text_input("Your Message", placeholder="Ask anything and hit Enter...")

if user_input:
    # Add user input to history
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Get response from GPT
    ai_reply = get_gpt_response(user_input)

    # Add assistant reply to history
    st.session_state.messages.append({"role": "assistant", "content": ai_reply})

    st.experimental_rerun()
