import streamlit as st
from groq import Groq

# Load API key securely from Streamlit Secrets
API_KEY = st.secrets["GROQ_API_KEY"]

# Initialize Groq client
client = Groq(api_key=API_KEY)

# Streamlit UI
st.set_page_config(page_title="IndiBot", page_icon="🤖")
st.title("🤖 IndiBot")
st.write("A simple chatbot built with Streamlit and Groq.")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Input box
if prompt := st.chat_input("Say something..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Get response from Groq
    with st.chat_message("assistant"):
        try:
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",  # or other Groq-supported model
                messages=[
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages
                ]
            )
            reply = response.choices[0].message.content
            st.markdown(reply)
        except Exception as e:
            reply = "⚠️ Error: " + str(e)
            st.markdown(reply)

    # Save assistant reply
    st.session_state.messages.append({"role": "assistant", "content": reply})
