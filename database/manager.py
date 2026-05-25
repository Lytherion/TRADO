import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import contextmanager


class DatabaseManager:

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        schema_path = Path(__file__).parent / "schema.sql"
        with open(schema_path, "r", encoding="utf-8") as f:
            schema_sql = f.read()
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        try:
            conn.executescript(schema_sql)
            # 迁移：删除已废弃列（SQLite 不支持 DROP COLUMN，用重建表方式）
            self._migrate(conn)
            conn.commit()
        finally:
            conn.close()

    def _migrate(self, conn):
        """迁移旧数据库：删除 due_time / snooze_until 列"""
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(tasks)")
        cols = {row[1] for row in cursor.fetchall()}

        if 'due_time' not in cols and 'snooze_until' not in cols:
            return  # 已是新结构，无需迁移

        conn.executescript("""
            BEGIN;
            CREATE TABLE IF NOT EXISTS tasks_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                start_time TEXT,
                remind_time TEXT,
                status INTEGER DEFAULT 0,
                tags TEXT,
                recurring_id INTEGER,
                notified INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT,
                completed_at TEXT,
                FOREIGN KEY (recurring_id) REFERENCES recurring_tasks(id) ON DELETE CASCADE
            );
            INSERT INTO tasks_new
                (id, title, description, start_time, remind_time,
                 status, tags, recurring_id, notified,
                 created_at, updated_at, completed_at)
            SELECT
                id, title, description, start_time,
                COALESCE(remind_time, due_time),
                status, tags, recurring_id, notified,
                created_at, updated_at, completed_at
            FROM tasks;
            DROP TABLE tasks;
            ALTER TABLE tasks_new RENAME TO tasks;
            CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
            CREATE INDEX IF NOT EXISTS idx_tasks_remind_time ON tasks(remind_time);
            CREATE INDEX IF NOT EXISTS idx_tasks_recurring_id ON tasks(recurring_id);
            COMMIT;
        """)

    @contextmanager
    def get_conn(self):
        conn = sqlite3.connect(
            self.db_path,
            timeout=30.0,
            check_same_thread=False,
            isolation_level=None
        )
        conn.row_factory = sqlite3.Row
        try:
            conn.execute('PRAGMA journal_mode=WAL')
            conn.execute('PRAGMA synchronous=NORMAL')
            yield conn
        finally:
            conn.close()

    def execute(self, sql: str, params: tuple = ()) -> int:
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            return cursor.lastrowid if sql.strip().upper().startswith("INSERT") else cursor.rowcount

    def query_one(self, sql: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            row = cursor.fetchone()
            return dict(row) if row else None

    def query_all(self, sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            return [dict(row) for row in cursor.fetchall()]

    # ========== 任务相关 ==========
    _TASK_COLUMNS = frozenset({
        "id", "title", "description", "start_time", "remind_time",
        "status", "tags", "recurring_id", "notified",
        "created_at", "updated_at", "completed_at",
    })

    def insert_task(self, task_dict: dict) -> int:
        fields = [k for k in task_dict if k in self._TASK_COLUMNS]
        placeholders = ",".join(["?"] * len(fields))
        sql = f"INSERT INTO tasks ({','.join(fields)}) VALUES ({placeholders})"
        return self.execute(sql, tuple(task_dict[k] for k in fields))

    def update_task(self, task_id: int, task_dict: dict) -> int:
        fields = [k for k in task_dict if k in self._TASK_COLUMNS]
        set_clause = ",".join([f"{k}=?" for k in fields])
        sql = f"UPDATE tasks SET {set_clause} WHERE id=?"
        return self.execute(sql, tuple(task_dict[k] for k in fields) + (task_id,))

    def delete_task(self, task_id: int) -> int:
        return self.execute("DELETE FROM tasks WHERE id=?", (task_id,))

    def get_task(self, task_id: int) -> Optional[dict]:
        return self.query_one("SELECT * FROM tasks WHERE id=?", (task_id,))

    def get_all_tasks(self, filters: Optional[dict] = None) -> List[dict]:
        sql = "SELECT * FROM tasks"
        params = []
        if filters:
            conditions = []
            for key, value in filters.items():
                if key not in self._TASK_COLUMNS:
                    raise ValueError(f"非法过滤字段: {key}")
                conditions.append(f"{key}=?")
                params.append(value)
            if conditions:
                sql += " WHERE " + " AND ".join(conditions)
        sql += " ORDER BY remind_time"
        return self.query_all(sql, tuple(params))

    def get_uncompleted_tasks(self) -> List[dict]:
        return self.query_all("SELECT * FROM tasks WHERE status = 0 ORDER BY remind_time")

    # ========== 循环任务相关 ==========
    _RECURRING_COLUMNS = frozenset({
        "id", "title", "description", "remind_time", "tags",
        "recur_type", "recur_interval", "recur_days", "recur_end_date",
        "last_generated_date", "next_generate_date", "is_active", "created_at",
    })

    def insert_recurring_task(self, task_dict: dict) -> int:
        fields = [k for k in task_dict if k in self._RECURRING_COLUMNS]
        placeholders = ",".join(["?"] * len(fields))
        sql = f"INSERT INTO recurring_tasks ({','.join(fields)}) VALUES ({placeholders})"
        return self.execute(sql, tuple(task_dict[k] for k in fields))

    def update_recurring_task(self, task_id: int, task_dict: dict) -> int:
        fields = [k for k in task_dict if k in self._RECURRING_COLUMNS]
        set_clause = ",".join([f"{k}=?" for k in fields])
        sql = f"UPDATE recurring_tasks SET {set_clause} WHERE id=?"
        return self.execute(sql, tuple(task_dict[k] for k in fields) + (task_id,))

    def delete_recurring_task(self, task_id: int) -> int:
        return self.execute("DELETE FROM recurring_tasks WHERE id=?", (task_id,))

    def get_recurring_task(self, task_id: int) -> Optional[dict]:
        return self.query_one("SELECT * FROM recurring_tasks WHERE id=?", (task_id,))

    def get_all_recurring_tasks(self, active_only: bool = True) -> List[dict]:
        sql = "SELECT * FROM recurring_tasks"
        if active_only:
            sql += " WHERE is_active=1"
        sql += " ORDER BY created_at"
        return self.query_all(sql)

    # ========== 配置相关 ==========
    def get_setting(self, key: str) -> Optional[str]:
        result = self.query_one("SELECT value FROM settings WHERE key=?", (key,))
        return result["value"] if result else None

    def set_setting(self, key: str, value: str):
        self.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?,?)", (key, value))

    # ========== 常驻任务相关 ==========
    def insert_permanent_task(self, task_data: dict) -> int:
        sql = """
        INSERT INTO permanent_tasks (title, description, tags, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?)
        """
        return self.execute(sql, (
            task_data["title"],
            task_data.get("description", ""),
            task_data.get("tags", ""),
            task_data["created_at"],
            task_data.get("updated_at")
        ))

    def update_permanent_task(self, task_id: int, task_data: dict):
        sql = """
        UPDATE permanent_tasks
        SET title=?, description=?, tags=?, updated_at=?
        WHERE id=?
        """
        self.execute(sql, (
            task_data["title"],
            task_data.get("description", ""),
            task_data.get("tags", ""),
            task_data.get("updated_at"),
            task_id
        ))

    def delete_permanent_task(self, task_id: int):
        return self.execute("DELETE FROM permanent_tasks WHERE id=?", (task_id,))

    def get_permanent_task(self, task_id: int) -> Optional[Dict[str, Any]]:
        return self.query_one("SELECT * FROM permanent_tasks WHERE id=?", (task_id,))

    def get_all_permanent_tasks(self, filters: dict = None) -> List[Dict[str, Any]]:
        return self.query_all("SELECT * FROM permanent_tasks ORDER BY created_at DESC")
