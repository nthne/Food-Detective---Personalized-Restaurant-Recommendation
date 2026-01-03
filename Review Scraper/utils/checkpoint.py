import json
import os

def load_checkpoint(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"last_index": 0, "results": []}


def save_checkpoint(path, index, results):
    with open(path, "w", encoding="utf-8") as f:
        json.dump({
            "last_index": index,
            "results": results
        }, f, ensure_ascii=False, indent=2)
