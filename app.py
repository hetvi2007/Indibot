import streamlit as st 
from datetime import datetime
import uuid
import json, os

# ---------- File Persistence ----------
STORE_FILE = "mehnitavi_store.json"

def load_store():
    if os.path.exists(STORE_FILE):
        with open(STORE_FILE, "r") as f:
            return json.load(f)
    return {"active": {}, "archived": {}}

def save_store():
    with open(STORE_FILE, "w") as f:
        json.dump(store, f)

# ---------- Page ----------
st.set_page_config(page_title="Mehnitavi", page_icon="🤖", layout="wide")

# ---------- Session Store ----------
store = st.session_state.setdefault("store", load_store())
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
    save_store()
    st.session_state.refresh = True

def open_chat(cid):
    st.session_state.current_id = cid
    st.session_state.refresh = True

def rename_chat(cid, new_title, bucket="active"):
    if new_title.strip():
        store[bucket][cid]["title"] = new_title.strip()
    save_store()
    st.session_state.refresh = True

def delete_chat(cid, bucket="active"):
    store[bucket].pop(cid, None)
    if bucket == "active" and st.session_state.current_id == cid:
        st.session_state.current_id = None
    save_store()
    st.session_state.refresh = True

def archive_chat(cid):
    store["archived"][cid] = store["active"].pop(cid)
    if st.session_state.current_id == cid:
        st.session_state.current_id = None
    save_store()
    st.session_state.refresh = True

def restore_chat(cid):
    store["active"][cid] = store["archived"].pop(cid)
    save_store()
    st.session_state.refresh = True

def export_text(cid, bucket="active"):
    chat = store[bucket][cid]
    lines = [f"Title: {chat['title']}", f"Created: {chat['created_at']}", "-"*40]
    for m in chat["messages"]:
        role = "You" if m["role"] == "user" else "Mehnitavi"
        lines.append(f"{role}: {m['content']}")
    return "\n".join(lines)

def autotitle_if_needed(cid):
    chat = store["active"][cid]
    if chat["title"] == "New Chat":
        for m in chat["messages"]:
            if m["role"] == "user" and m["content"].strip():
                chat["title"] = m["content"].strip()[:40]
                break
    save_store()
    st.session_state.refresh = True

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
                with st.popover("⋮"):  # ✅ cleaner 3-dots menu
                    new_name = st.text_input("Rename", value=chat["title"], key=f"rn_{cid}")
                    if st.button("💾 Save name", key=f"rns_{cid}"):
                        rename_chat(cid, new_name, bucket="active")
                    st.download_button(
                        "⬇️ Download (.txt)",
                        data=export_text(cid, bucket="active"),
                        file_name=f"{(chat['title'] or 'Mehnitavi_chat')}.txt",
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
                            file_name=f"{(chat['title'] or 'Mehnitavi_chat')}.txt",
                            key=f"adl_{cid}",
                            use_container_width=True,
                        )
                        if st.button("↩️ Restore", key=f"res_{cid}"):
                            restore_chat(cid)
                        if st.button("🗑️ Delete", key=f"adel_{cid}"):
                            delete_chat(cid, bucket="archived")

# ---------- Main area ----------
st.title("🤖 Mehnitavi")

if current_id and current_id in store["active"]:
    chat = store["active"][current_id]

    # show messages
    for m in chat["messages"]:
        if m["role"] == "user":
            with st.chat_message("user", avatar="🧑"):
                st.write(m["content"])
        else:
            with st.chat_message("assistant", avatar="🦾"):
                st.write(m["content"])

    # input
    text = st.chat_input("Say something…")
    if text:
        chat["messages"].append({"role": "user", "content": text})

        # Mehnitavi reply (no "Mehnitavi:" prefix inside the message)
        reply = f"{text}"
        chat["messages"].append({"role": "assistant", "content": reply})

        autotitle_if_needed(current_id)
        save_store()
        st.session_state.refresh = True
else:
    st.info("Start a new chat from the sidebar.")

# ---------- Handle Refresh ----------
if st.session_state.get("refresh", False):
    st.session_state.refresh = False
    st.rerun()
