import streamlit as st
import openai

# --- Setup your OpenAI key ---
openai.api_key = "YOUR_OPENAI_API_KEY"  # replace with your key

st.set_page_config(page_title="IndiBot", page_icon="🤖")
st.title("🤖 IndiBot")
st.write("Now powered with AI (OpenAI GPT)!")

# Store chat history
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# User input
user_input = st.chat_input("Ask me anything...")

if user_input:
    # Save user input
    st.session_state["messages"].append({"role": "user", "content": user_input})

    # Send to GPT model
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",   # you can use "gpt-4" if available
        messages=st.session_state["messages"]
    )

    bot_reply = response["choices"][0]["message"]["content"]
    st.session_state["messages"].append({"role": "assistant", "content": bot_reply})

# Display messages
for msg in st.session_state["messages"]:
    if msg["role"] == "user":
        st.markdown(f"🧑 **You:** {msg['content']}")
    else:
        st.markdown(f"🤖 **IndiBot:** {msg['content']}")
