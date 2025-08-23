import streamlit as st

# --- Basic ChatBot Class ---
class ChatBot:
    def __init__(self, name="IndiBot"):
        self.name = name

    def get_response(self, user_input):
        # Very simple rule-based responses
        user_input = user_input.lower()

        if "hello" in user_input or "hi" in user_input:
            return "Hello 👋! How can I help you today?"
        elif "your name" in user_input:
            return f"My name is {self.name} 🤖"
        elif "bye" in user_input:
            return "Goodbye! Have a great day 🌸"
        else:
            return "I’m still learning... can you rephrase that?"

# --- Streamlit UI ---
st.set_page_config(page_title="IndiBot", page_icon="🤖")

st.title("🤖 IndiBot")
st.write("A simple chatbot built with Streamlit and Python.")

# Initialize bot
bot = ChatBot()

# Store conversation in session_state
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# Chat input
user_input = st.chat_input("Say something...")

if user_input:
    # Store user message
    st.session_state["messages"].append({"role": "user", "content": user_input})

    # Get bot response
    response = bot.get_response(user_input)
    st.session_state["messages"].append({"role": "bot", "content": response})

# Display chat history
for msg in st.session_state["messages"]:
    if msg["role"] == "user":
        st.markdown(f"🧑 **You:** {msg['content']}")
    else:
        st.markdown(f"🤖 **{bot.name}:** {msg['content']}")

