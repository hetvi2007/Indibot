import streamlit as st
from datetime import datetime
import uuid
import os
import re
from groq import Groq

# ---------- Setup ----------
st.set_page_config(page_title="IndiBot", page_icon="🤖", layout="wide")

# Initialize Groq client
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# ---------- Session Store ----------
store = st.session_state.setdefault("store", {"active": {}, "archived": {}})
current_id = st.session_state.setdefault("current_id", None)

# ---------- Helpers ----------
def new_chat():
    cid = uuid.uuid4().hex[:8]
    store["active"][cid] = {
        "title": "New Chat",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "messages": []
    }
    st.session_state.current_id = cid

def open_chat(cid):
    st.session_state.current_id = cid

def rename_chat(cid, new_title, bucket="active"):
    if new_title.strip():
        store[bucket][cid]["title"] = new_title.strip()

def delete_chat(cid, bucket="active"):
    store[bucket].pop(cid, None)
    if bucket == "active" and st.session_state.current_id == cid:
        st.session_state.current_id = None

def archive_chat(cid):
    store["archived"][cid] = store["active"].pop(cid)
    if st.session_state.current_id == cid:
        st.session_state.current_id = None

def restore_chat(cid):
    store["active"][cid] = store["archived"].pop(cid)

def export_text(cid, bucket="active"):
    chat = store[bucket][cid]
    lines = [f"Title: {chat['title']}", f"Created: {chat['created_at']}", "-"*40]
    for m in chat["messages"]:
        lines.append(f"{m['role'].capitalize()}: {m['content']}")
    return "\n".join(lines)

def autotitle_if_needed(cid):
    chat = store["active"][cid]
    if chat["title"] == "New Chat":
        for m in chat["messages"]:
            if m["role"] == "user" and m["content"].strip():
                chat["title"] = m["content"].strip()[:40]
                break

def highlight_text(text, term):
    """Highlight search term in text."""
    if not term:
        return text
    pattern = re.compile(re.escape(term), re.IGNORECASE)
    return pattern.sub(lambda m: f"<mark>{m.group(0)}</mark>", text)

# ---------- Sidebar ----------
with st.sidebar:
    st.header("Options")
    st.button("✍️ New chat", use_container_width=True, on_click=new_chat)

    st.markdown("---")
    st.subheader("Chats")

    # Active chats
    if not store["active"]:
        st.caption("No chats yet. Start one!")
    else:
        for cid, chat in list(store["active"].items())[::-1]:
            c1, c2 = st.columns([0.8, 0.2])
            if c1.button(chat["title"] or "Untitled", key=f"open_{cid}", use_container_width=True):
                open_chat(cid)
            with c2:
                with st.popover("⋮"):
                    new_name = st.text_input("Rename", value=chat["title"], key=f"rn_{cid}")
                    if st.button("💾 Save name", key=f"rns_{cid}"):
                        rename_chat(cid, new_name, bucket="active")
                    st.download_button(
                        "⬇️ Download (.txt)",
                        data=export_text(cid, bucket="active"),
                        file_name=f"{(chat['title'] or 'chat')}.txt",
                        key=f"dl_{cid}",
                        use_container_width=True,
                    )
                    if st.button("📦 Archive", key=f"arc_{cid}"):
                        archive_chat(cid)
                    if st.button("🗑️ Delete", key=f"del_{cid}"):
                        delete_chat(cid, bucket="active")

    # Archived chats
    if store["archived"]:
        with st.expander("🗂️ Library"):
            for cid, chat in list(store["archived"].items())[::-1]:
                c1, c2 = st.columns([0.8, 0.2])
                c1.write(f"📄 {chat['title'] or 'Untitled'}")
                with c2:
                    with st.popover("⋮"):
                        new_name = st.text_input("Rename", value=chat["title"], key=f"arn_{cid}")
                        if st.button("💾 Save name", key=f"arns_{cid}"):
                            rename_chat(cid, new_name, bucket="archived")
                        st.download_button(
                            "⬇️ Download (.txt)",
                            data=export_text(cid, bucket="archived"),
                            file_name=f"{(chat['title'] or 'chat')}.txt",
                            key=f"adl_{cid}",
                            use_container_width=True,
                        )
                        if st.button("↩️ Restore", key=f"res_{cid}"):
                            restore_chat(cid)
                        if st.button("🗑️ Delete", key=f"adel_{cid}"):
                            delete_chat(cid, bucket="archived")

# ---------- Main Area ----------
st.title("🤖 IndiBot (Mehnitavi)")

if current_id and current_id in store["active"]:
    chat = store["active"][current_id]

    # 🔹 Clear chat
    if st.button("🧹 Clear all messages in this chat"):
        chat["messages"] = []
        st.rerun()

    # 🔎 Search messages
    search_term = st.text_input("🔍 Search messages", key="search_box")
    if search_term.strip():
        filtered_messages = [
            (idx, m) for idx, m in enumerate(chat["messages"])
            if search_term.lower() in m["content"].lower()
        ]
        st.caption(f"Showing {len(filtered_messages)} result(s) for '{search_term}'")
    else:
        filtered_messages = list(enumerate(chat["messages"]))

    # ---------- Show messages ----------
    for idx, m in filtered_messages:
        role = "user" if m["role"] == "user" else "assistant"
        with st.chat_message(role):
            # highlight content if searching
            if search_term.strip():
                highlighted = highlight_text(m["content"], search_term)
                st.markdown(highlighted, unsafe_allow_html=True)
            else:
                st.write(m["content"])

            c1, c2, c3, c4 = st.columns([0.2, 0.2, 0.2, 0.2])

            # Edit
            with c1:
                if st.button("✏️ Edit", key=f"edit_{idx}"):
                    st.session_state[f"editing_{idx}"] = True

            # Copy
            with c2:
                copy_code = f"""
                <script>
                function copyToClipboard_{idx}() {{
                    navigator.clipboard.writeText(`{m["content"]}`);
                    alert("Copied to clipboard!");
                }}
                </script>
                <button onclick="copyToClipboard_{idx}()">📋 Copy</button>
                """
                st.markdown(copy_code, unsafe_allow_html=True)

            # Resend (only for user)
            if role == "user":
                with c3:
                    if st.button("🔄 Resend", key=f"resend_{idx}"):
                        st.session_state[f"editing_resend_{idx}"] = True

            # Delete
            with c4:
                if st.button("🗑️ Delete", key=f"delete_{idx}"):
                    chat["messages"].pop(idx)
                    st.rerun()

            # Edit mode
            if st.session_state.get(f"editing_{idx}", False):
                new_text = st.text_area("Edit message:", value=m["content"], key=f"editbox_{idx}")
                if st.button("💾 Save", key=f"save_{idx}"):
                    chat["messages"][idx]["content"] = new_text
                    st.session_state[f"editing_{idx}"] = False
                    st.rerun()

            # Resend mode
            if st.session_state.get(f"editing_resend_{idx}", False):
                new_text = st.text_area("Edit & resend:", value=m["content"], key=f"editresendbox_{idx}")
                if st.button("🚀 Resend", key=f"doresend_{idx}"):
                    chat["messages"][idx]["content"] = new_text
                    chat["messages"] = chat["messages"][: idx + 1]  # truncate after this msg

                    # Ask Mehnitavi again
                    try:
                        response = client.chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            messages=[{"role": "system", "content": "You are Mehnitavi, a helpful assistant."}]
                                     + chat["messages"],
                        )
                        reply = response.choices[0].message.content
                    except Exception:
                        response = client.chat.completions.create(
                            model="llama-3.1-8b-instant",
                            messages=[{"role": "system", "content": "You are Mehnitavi, a helpful assistant."}]
                                     + chat["messages"],
                        )
                        reply = response.choices[0].message.content

                    chat["messages"].append({"role": "assistant", "content": reply})
                    st.session_state[f"editing_resend_{idx}"] = False
                    st.rerun()

    # ---------- Input ----------
    text = st.chat_input("Ask Mehnitavi something…")
    if text:
        # save user msg
        chat["messages"].append({"role": "user", "content": text})

        # send to Groq
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": "You are Mehnitavi, a helpful assistant."}]
                         + chat["messages"],
            )
            reply = response.choices[0].message.content
        except Exception:
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "system", "content": "You are Mehnitavi, a helpful assistant."}]
                         + chat["messages"],
            )
            reply = response.choices[0].message.content

        # save AI reply
        chat["messages"].append({"role": "assistant", "content": reply})

        autotitle_if_needed(current_id)
        st.rerun()
else:
    st.info("Start a new chat from the sidebar.")
