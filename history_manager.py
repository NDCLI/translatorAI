import json
import os
from datetime import datetime

class HistoryManager:
    def __init__(self, filename="history.json", max_entries=50):
        self.filename = filename
        self.max_entries = max_entries
        self.history = self.load_history()

    def load_history(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading history: {e}")
                return []
        return []

    def add_entry(self, source_text, target_text, source_lang, target_lang):
        entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "source": source_text,
            "target": target_text,
            "src_lang": source_lang,
            "dest_lang": target_lang
        }
        self.history.insert(0, entry) # Add to top
        # Keep only max_entries
        self.history = self.history[:self.max_entries]
        self.save_history()

    def save_history(self):
        try:
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Error saving history: {e}")

    def clear_history(self):
        self.history = []
        if os.path.exists(self.filename):
            os.remove(self.filename)

    def get_history(self):
        return self.history
