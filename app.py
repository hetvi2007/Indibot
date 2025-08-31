import streamlit as st
from datetime import datetime
import uuid
import os
import re
import json
import html as html_lib
import streamlit.components.v1 as components
from groq import Groq

# ---------- Setup ----------
st.set_page_config(page_title="IndiBot", page_icon="🤖", layout="wide")

# Initialize Groq client (ensure GROQ_API_KEY is set)
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

def clear_current_chat(cid):
    if cid in store["active"]:
        store["active"][cid]["messages"] = []

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
    """Escapes HTML, then highlights matches with <mark>."""
    if not term:
        return html_lib.escape(text)
    escaped = html_lib.escape(text)
    pattern = re.compile(re.escape(term), re.IGNORECASE)
    return pattern.sub(lambda m: f"<mark>{m.group(0)}</mark>", escaped)

def copy_button(text: str, key: str):
    """
    Renders a real 'Copy to clipboard' button (like ChatGPT) using a tiny
    in-page script. Works locally and typically on Streamlit Cloud.
    """
    js_text = json.dumps(text)  # safe for JS (handles quotes/newlines)
    btn_id = f"copy_btn_{key}"
    components.html(
        f"""
        <button id="{btn_id}" style="padding:6px 10px;border:1px solid #ccc;border-radius:8px;cursor:pointer">
            📋 Copy
        </button>
        <script>
        (function(){{
            const btn = document.getElementById("{btn_id}");
            if(!btn) return;
            btn.addEventListener("click", async () => {{
                try {{
                    await navigator.clipboard.writeText({js_text});
                    const old = btn.innerText;
                    btn.innerText = "✅ Copied";
                    setTimeout(() => btn.innerText = old, 1200);
                }} catch (e) {{
                    // Fallback for older browsers
                    const ta = document.createElement('textarea');
                    ta.value = {js_text};
                    document.body.appendChild(ta);
                    ta.select();
                    document.execCommand('copy');
                    document.body.removeChild(ta);
                }}
            }});
        }})();
        </script>
        """,
        height=46,
    )

def ask_mehnitavi(messages):
    """Call Groq with a supported model and return assistant text."""
    try:
        resp = client.chat.completions.create(
            model="llama-3.1-8b-instant",  # stable Groq model
            messages=[{"role": "system", "content": "You are Mehnitavi, a helpful assistant."}] + messages,
        )
        return resp.choices[0].message.content
    except Exception as e:
        return f"⚠️ Error talking to Mehnitavi: {e}"

# ---------- Sidebar ----------
with st.sidebar:
    st.header("Options")
    st.button("✍️ New chat", use_container_width=True, on_click=new_chat)

    if current_id:
        st.button("🧹 Clear this chat", use_container_width=True,
                  on_click=lambda: clear_current_chat(current_id))

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

    # Top-level clear in main area too
    if st.button("🧹 Clear all messages in this chat", key="clear_top"):
        chat["messages"] = []
        st.rerun()

    # 🔎 Search + highlight
    search_term = st.text_input("🔍 Search messages", key="search_box")
    if search_term.strip():
        filtered = [(i, m) for i, m in enumerate(chat["messages"])
                    if search_term.lower() in m["content"].lower()]
        st.caption(f"Showing {len(filtered)} result(s) for '{search_term}'")
    else:
        filtered = list(enumerate(chat["messages"]))

    # ---------- Render messages ----------
    for idx, m in filtered:
        role = "user" if m["role"] == "user" else "assistant"
        with st.chat_message(role):
            if search_term.strip():
                st.markdown(highlight_text(m["content"], search_term), unsafe_allow_html=True)
            else:
                st.write(m["content"])

            c1, c2, c3, c4 = st.columns([0.25, 0.2, 0.2, 0.2])

            # Edit (assistant) or Edit & Resend (user)
            with c1:
                if role == "user":
                    if st.button("✏️ Edit & Resend", key=f"edit_{idx}"):
                        st.session_state[f"editing_{idx}"] = True
                else:
                    if st.button("✏️ Edit", key=f"edit_{idx}"):
                        st.session_state[f"editing_{idx}"] = True

            # Copy to clipboard (real)
            with c2:
                copy_button(m["content"], key=str(idx))

            # Resend (quick) for user (without editing)
            if role == "user":
                with c3:
                    if st.button("🔄 Resend", key=f"resend_quick_{idx}"):
                        chat["messages"] = chat["messages"][: idx + 1]
                        reply = ask_mehnitavi(chat["messages"])
                        chat["messages"].append({"role": "assistant", "content": reply})
                        st.rerun()

            # Delete message
            with c4:
                if st.button("🗑️ Delete", key=f"delete_{idx}"):
                    chat["messages"].pop(idx)
                    st.rerun()

            # Edit / Edit & Resend pane
            if st.session_state.get(f"editing_{idx}", False):
                new_text = st.text_area("Edit message:", value=m["content"], key=f"editbox_{idx}")
                csa, csb = st.columns([0.4, 0.6])
                with csa:
                    if st.button("💾 Save", key=f"save_{idx}"):
                        chat["messages"][idx]["content"] = new_text
                        st.session_state[f"editing_{idx}"] = False
                        st.rerun()
                # For user: Save & Resend in one go
                if role == "user":
                    with csb:
                        if st.button("🚀 Save & Resend", key=f"saveresend_{idx}"):
                            chat["messages"][idx]["content"] = new_text
                            chat["messages"] = chat["messages"][: idx + 1]
                            reply = ask_mehnitavi(chat["messages"])
                            chat["messages"].append({"role": "assistant", "content": reply})
                            st.session_state[f"editing_{idx}"] = False
                            st.rerun()

    # ---------- Input ----------
    text = st.chat_input("Ask Mehnitavi something…")
    if text:
        chat["messages"].append({"role": "user", "content": text})
        reply = ask_mehnitavi(chat["messages"])
        chat["messages"].append({"role": "assistant", "content": reply})
        autotitle_if_needed(current_id)
        st.rerun()
else:
    st.info("Start a new chat from the sidebar.")
