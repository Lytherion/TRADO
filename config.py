import os
from pathlib import Path

APP_DATA_DIR = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
BASE_DIR = APP_DATA_DIR / "TaskManager"
BASE_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = BASE_DIR / "tasks.db"
