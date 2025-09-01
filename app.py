import streamlit as st

st.set_page_config(page_title="Mehnitavi", page_icon="🤖")

# --- App Title ---
st.markdown("<h1 style='font-family: Arial;'>🤖 Mehnitavi</h1>", unsafe_allow_html=True)

# --- Initialize Chat History ---
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# --- Display Chat Messages ---
for message in st.session_state["messages"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        st.markdown(
            """
            <div style='display: flex; gap: 15px; margin-top: 5px; font-size: 18px; color: gray;'>
                <span title='Copy'>📋</span>
                <span title='Like'>👍</span>
                <span title='Dislike'>👎</span>
                <span title='Speak'>🔊</span>
                <span title='Share'>⤴️</span>
                <span title='Refresh'>🔄</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

# --- Input Section ---
col1, col2 = st.columns([0.15, 0.85])

with col1:
    uploaded_file = st.file_uploader(
        "",
        type=["png", "jpg", "jpeg", "pdf", "txt", "mp3", "wav"],
        label_visibility="collapsed",
    )
    st.caption("📎 Upload")

with col2:
    text = st.chat_input("Ask Mehnitavi something…")

# --- Handle User Input ---
if text:
    # User message
    st.session_state["messages"].append({"role": "user", "content": text})
    with st.chat_message("user"):
        st.markdown(text)

    # Bot response (dummy for now)
    response = f"Hello! You said: **{text}**"
    st.session_state["messages"].append({"role": "assistant", "content": response})

    with st.chat_message("assistant"):
        st.markdown(response)
        st.markdown(
            """
            <div style='display: flex; gap: 15px; margin-top: 5px; font-size: 18px; color: gray;'>
                <span title='Copy'>📋</span>
                <span title='Like'>👍</span>
                <span title='Dislike'>👎</span>
                <span title='Speak'>🔊</span>
                <span title='Share'>⤴️</span>
                <span title='Refresh'>🔄</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
