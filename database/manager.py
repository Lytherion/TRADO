"""
数据库管理器
"""
import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import contextmanager


class DatabaseManager:
    """数据库管理器"""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """初始化数据库"""
        schema_path = Path(__file__).parent / "schema.sql"
        with open(schema_path, "r", encoding="utf-8") as f:
            schema_sql = f.read()

        # 临时创建一个连接来初始化数据库
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        try:
            conn.executescript(schema_sql)
            conn.commit()
        finally:
            conn.close()

    @contextmanager
    def get_conn(self):
        """获取数据库连接（上下文管理器）"""
        # 设置超时避免死锁,启用 WAL 模式提高并发性能
        conn = sqlite3.connect(
            self.db_path,
            timeout=30.0,  # 30秒超时
            check_same_thread=False,  # 允许多线程使用
            isolation_level=None  # 自动提交模式,减少锁冲突
        )
        conn.row_factory = sqlite3.Row  # 返回字典格式
        try:
            # 启用 WAL 模式(Write-Ahead Logging)提高并发性能
            conn.execute('PRAGMA journal_mode=WAL')
            conn.execute('PRAGMA synchronous=NORMAL')  # 平衡性能和安全
            yield conn
        finally:
            conn.close()

    def execute(self, sql: str, params: tuple = ()) -> int:
        """执行SQL（增删改），返回影响行数或lastrowid"""
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            # isolation_level=None 时自动提交,无需手动 commit
            return cursor.lastrowid if sql.strip().upper().startswith("INSERT") else cursor.rowcount

    def query_one(self, sql: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        """查询单条记录"""
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            row = cursor.fetchone()
            return dict(row) if row else None

    def query_all(self, sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """查询多条记录"""
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            return [dict(row) for row in cursor.fetchall()]

    # ========== 任务相关 ==========
    def insert_task(self, task_dict: dict) -> int:
        """插入任务"""
        fields = [k for k in task_dict if k in self._TASK_COLUMNS]
        placeholders = ",".join(["?"] * len(fields))
        sql = f"INSERT INTO tasks ({','.join(fields)}) VALUES ({placeholders})"
        return self.execute(sql, tuple(task_dict[k] for k in fields))

    def update_task(self, task_id: int, task_dict: dict) -> int:
        """更新任务"""
        fields = [k for k in task_dict if k in self._TASK_COLUMNS]
        set_clause = ",".join([f"{k}=?" for k in fields])
        sql = f"UPDATE tasks SET {set_clause} WHERE id=?"
        return self.execute(sql, tuple(task_dict[k] for k in fields) + (task_id,))

    def delete_task(self, task_id: int) -> int:
        """删除任务"""
        return self.execute("DELETE FROM tasks WHERE id=?", (task_id,))

    def get_task(self, task_id: int) -> Optional[dict]:
        """获取单个任务"""
        return self.query_one("SELECT * FROM tasks WHERE id=?", (task_id,))

    _TASK_COLUMNS = frozenset({
        "id", "title", "description", "start_time", "due_time", "remind_time",
        "status", "tags", "recurring_id", "notified", "snooze_until",
        "created_at", "updated_at", "completed_at",
    })

    def get_all_tasks(self, filters: Optional[dict] = None) -> List[dict]:
        """获取所有任务（支持过滤）"""
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

        sql += " ORDER BY due_time"
        return self.query_all(sql, tuple(params))

    def get_uncompleted_tasks(self) -> List[dict]:
        """获取未完成的任务(status = 0)"""
        sql = "SELECT * FROM tasks WHERE status = 0 ORDER BY due_time"
        return self.query_all(sql)

    # ========== 循环任务相关 ==========
    _RECURRING_COLUMNS = frozenset({
        "id", "title", "description", "remind_time", "tags",
        "recur_type", "recur_interval", "recur_days", "recur_end_date",
        "last_generated_date", "next_generate_date", "is_active", "created_at",
    })

    def insert_recurring_task(self, task_dict: dict) -> int:
        """插入循环任务"""
        fields = [k for k in task_dict if k in self._RECURRING_COLUMNS]
        placeholders = ",".join(["?"] * len(fields))
        sql = f"INSERT INTO recurring_tasks ({','.join(fields)}) VALUES ({placeholders})"
        return self.execute(sql, tuple(task_dict[k] for k in fields))

    def update_recurring_task(self, task_id: int, task_dict: dict) -> int:
        """更新循环任务"""
        fields = [k for k in task_dict if k in self._RECURRING_COLUMNS]
        set_clause = ",".join([f"{k}=?" for k in fields])
        sql = f"UPDATE recurring_tasks SET {set_clause} WHERE id=?"
        return self.execute(sql, tuple(task_dict[k] for k in fields) + (task_id,))

    def delete_recurring_task(self, task_id: int) -> int:
        """删除循环任务"""
        return self.execute("DELETE FROM recurring_tasks WHERE id=?", (task_id,))

    def get_recurring_task(self, task_id: int) -> Optional[dict]:
        """获取单个循环任务"""
        return self.query_one("SELECT * FROM recurring_tasks WHERE id=?", (task_id,))

    def get_all_recurring_tasks(self, active_only: bool = True) -> List[dict]:
        """获取所有循环任务"""
        sql = "SELECT * FROM recurring_tasks"
        if active_only:
            sql += " WHERE is_active=1"
        sql += " ORDER BY created_at"
        return self.query_all(sql)

    # ========== 配置相关 ==========
    def get_setting(self, key: str) -> Optional[str]:
        """获取配置"""
        result = self.query_one("SELECT value FROM settings WHERE key=?", (key,))
        return result["value"] if result else None

    def set_setting(self, key: str, value: str):
        """设置配置"""
        sql = "INSERT OR REPLACE INTO settings (key, value) VALUES (?,?)"
        self.execute(sql, (key, value))

    # ========== 常驻任务相关 ==========
    def insert_permanent_task(self, task_data: dict) -> int:
        """插入常驻任务"""
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
        """更新常驻任务"""
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
        """删除常驻任务"""
        return self.execute("DELETE FROM permanent_tasks WHERE id=?", (task_id,))

    def get_permanent_task(self, task_id: int) -> Optional[Dict[str, Any]]:
        """获取单个常驻任务"""
        return self.query_one("SELECT * FROM permanent_tasks WHERE id=?", (task_id,))

    def get_all_permanent_tasks(self, filters: dict = None) -> List[Dict[str, Any]]:
        """获取所有常驻任务"""
        sql = "SELECT * FROM permanent_tasks ORDER BY created_at DESC"
        return self.query_all(sql)
