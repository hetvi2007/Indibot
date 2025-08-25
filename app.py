# app.py
import time
import streamlit as st
from groq import Groq

# -------------------- PAGE CONFIG --------------------
st.set_page_config(page_title="IndiBot", page_icon="🤖", layout="centered")

# -------------------- SAFE CLIENT INIT --------------------
def make_client():
    try:
        api_key = st.secrets["GROQ_API_KEY"]  # key is NOT hardcoded
        return Groq(api_key=api_key)
    except Exception as e:
        st.error("❌ GROQ_API_KEY is missing in Streamlit secrets. "
                 "Add it in Settings → Secrets (or .streamlit/secrets.toml).")
        st.stop()

client = make_client()

# -------------------- SIDEBAR CONTROLS --------------------
st.sidebar.header("⚙️ Settings")

persona = st.sidebar.selectbox(
    "Personality",
    [
        "Helpful General Assistant",
        "Friendly Teacher",
        "Professional Support Agent",
        "Playful Buddy",
        "Strict Coach"
    ],
    index=0,
)

temperature = st.sidebar.slider("Creativity (temperature)", 0.0, 1.0, 0.3, 0.1)

if st.sidebar.button("🧹 Clear chat"):
    st.session_state.pop("messages", None)
    st.experimental_rerun()

# -------------------- SYSTEM PROMPTS --------------------
PERSONA_PROMPTS = {
    "Helpful General Assistant": "You are IndiBot, a concise, helpful assistant. Be clear and kind.",
    "Friendly Teacher": "You are IndiBot, a friendly teacher. Explain step-by-step and check understanding.",
    "Professional Support Agent": "You are IndiBot, a professional support agent. Be brief, polite, and action-oriented.",
    "Playful Buddy": "You are IndiBot, playful and upbeat. Use light emojis sparingly and keep responses helpful.",
    "Strict Coach": "You are IndiBot, a tough but fair coach. Be direct, focused on goals and next actions."
}

system_prompt = PERSONA_PROMPTS[persona]

# -------------------- STATE: CHAT HISTORY --------------------
if "messages" not in st.session_state:
    st.session_state.messages = []  # only user/assistant pairs; system added per call below

# -------------------- HEADER --------------------
st.title("🤖 IndiBot")
st.caption("Chatbot powered by **Groq** + **Streamlit** · Multi-turn · Personalities · Downloadable chat")

# -------------------- RENDER HISTORY --------------------
for m in st.session_state.messages:
    role = m["role"]
    avatar = "👤" if role == "user" else "🤖"
    with st.chat_message(role, avatar=avatar):
        st.markdown(m["content"])

# -------------------- INPUT --------------------
prompt = st.chat_input("Say something…")
if prompt:
    # show user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    # build messages with system prompt + history
    convo = [{"role": "system", "content": system_prompt}] + [
        {"role": m["role"], "content": m["content"]} for m in st.session_state.messages
    ]

    # assistant typing
    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("IndiBot is thinking…"):
            try:
                resp = client.chat.completions.create(
                    model="llama3-8b-8192",        # you can use another Groq model here
                    messages=convo,
                    temperature=temperature
                )
                reply = resp.choices[0].message.content
            except Exception as e:
                reply = f"⚠️ Error while contacting Groq: {e}"
            # small delay for nicer UX
            time.sleep(0.2)
            st.markdown(reply)

    # save assistant reply
    st.session_state.messages.append({"role": "assistant", "content": reply})

# -------------------- DOWNLOAD CHAT --------------------
def build_transcript() -> str:
    lines = [f"IndiBot Transcript — Persona: {persona}\n"]
    for m in st.session_state.messages:
        speaker = "You" if m["role"] == "user" else "IndiBot"
        lines.append(f"{speaker}: {m['content']}\n")
    return "\n".join(lines) if st.session_state.messages else "No messages yet."

st.download_button(
    label="💾 Download chat (.txt)",
    data=build_transcript().encode("utf-8"),
    file_name="indibot_chat.txt",
    mime="text/plain",
    use_container_width=True
)
