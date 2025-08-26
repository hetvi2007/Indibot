import streamlit as st
import json, os, uuid
from datetime import datetime
from pathlib import Path
from contextlib import contextmanager

st.set_page_config(page_title="IndiBot", page_icon="🤖", layout="wide")

# ---------------- Storage ----------------
CHAT_FILE = "chats.json"

def load_store():
    if Path(CHAT_FILE).exists():
        try:
            with open(CHAT_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"active": {}, "archived": {}}

def save_store(store):
    with open(CHAT_FILE, "w") as f:
        json.dump(store, f, indent=2)

store = st.session_state.setdefault("store", load_store())
current_id = st.session_state.setdefault("current_id", None)

# ---------------- Helpers ----------------
def new_chat():
    cid = uuid.uuid4().hex[:8]
    store["active"][cid] = {
        "title": "New Chat",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "messages": []
    }
    st.session_state.current_id = cid
    save_store(store); st.rerun()

def open_chat(cid):
    st.session_state.current_id = cid
    st.rerun()

def delete_chat(cid, archived=False):
    bucket = "archived" if archived else "active"
    store[bucket].pop(cid, None)
    if st.session_state.current_id == cid and not archived:
        st.session_state.current_id = None
    save_store(store); st.rerun()

def archive_chat(cid):
    store["archived"][cid] = store["active"].pop(cid)
    if st.session_state.current_id == cid:
        st.session_state.current_id = None
    save_store(store); st.rerun()

def restore_chat(cid):
    store["active"][cid] = store["archived"].pop(cid)
    save_store(store); st.rerun()

def rename_chat(cid, new_title, archived=False):
    bucket = "archived" if archived else "active"
    store[bucket][cid]["title"] = new_title.strip() or store[bucket][cid]["title"]
    save_store(store); st.rerun()

def export_text(cid, archived=False):
    bucket = "archived" if archived else "active"
    chat = store[bucket][cid]
    lines = [f"Title: {chat['title']}", f"Created: {chat['created_at']}", "-"*40]
    for m in chat["messages"]:
        lines.append(f"{m['role'].capitalize()}: {m['content']}")
    return "\n".join(lines)

def autotitle_if_needed(cid):
    chat = store["active"][cid]
    if chat["title"] == "New Chat":
        for m in chat["messages"]:
            if m["role"] == "user":
                chat["title"] = (m["content"].strip() or "Untitled")[:40]
                break
        save_store(store)

@contextmanager
def dotmenu(label="⋮"):
    if hasattr(st, "popover"):
        with st.popover(label):
            yield
    else:
        with st.expander(label):
            yield

# ---------------- Sidebar ----------------
with st.sidebar:
    st.header("Options")
    st.button("✍️ New chat", on_click=new_chat, use_container_width=True)

    st.markdown("---")
    st.subheader("Chats")

    if not store["active"]:
        st.caption("No chats yet. Start one!")
    else:
        for cid, chat in list(store["active"].items()):
            c1, c2 = st.columns([0.85, 0.15])
            if c1.button(chat["title"], key=f"open_{cid}", use_container_width=True):
                open_chat(ci_
