import json
import os

SAVE_PATH = "lifeforge_save.json"

def has_save():
    try:
        return os.path.exists(SAVE_PATH)
    except Exception:
        return False

def save_game(data):
    """Best effort: in a browser build the file may not survive a reload."""
    try:
        with open(SAVE_PATH, "w") as f:
            json.dump(data, f)
    except Exception:
        pass

def load_game():
    try:
        with open(SAVE_PATH) as f:
            return json.load(f)
    except Exception:
        return None

def delete_save():
    try:
        if os.path.exists(SAVE_PATH):
            os.remove(SAVE_PATH)
    except Exception:
        pass
