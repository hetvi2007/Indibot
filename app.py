def load_chats():
    if os.path.exists("chats.json"):
        with open("chats.json", "r") as f:
            return json.load(f)
    return []   # Return empty if no file yet

def save_chats(chats):
    with open("chats.json", "w") as f:
        json.dump(chats, f, indent=2)
