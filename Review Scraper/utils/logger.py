import json
import os
from datetime import datetime

def log_error(path, url, index, error):
    logs = []
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            logs = json.load(f)

    logs.append({
        "url": url,
        "index": index,
        "error": str(error),
        "time": datetime.now().isoformat()
    })

    with open(path, "w", encoding="utf-8") as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)
