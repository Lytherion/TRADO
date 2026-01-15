"""
普通任务模型
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from .enums import TaskStatus


@dataclass
class Task:
    """普通任务"""

    # 基本信息
    title: str = ""
    description: str = ""

    # 时间
    start_time: Optional[datetime] = None
    due_time: Optional[datetime] = None
    remind_time: Optional[datetime] = None

    # 属性
    status: TaskStatus = TaskStatus.TODO
    tags: List[str] = field(default_factory=list)

    # 关联
    id: Optional[int] = None
    recurring_id: Optional[int] = None  # 所属循环任务

    # 提醒
    notified: bool = False
    snooze_until: Optional[datetime] = None

    # 元数据
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "due_time": self.due_time.isoformat() if self.due_time else None,
            "remind_time": self.remind_time.isoformat() if self.remind_time else None,
            "status": self.status.value,
            "tags": ",".join(self.tags) if self.tags else "",
            "recurring_id": self.recurring_id,
            "notified": 1 if self.notified else 0,
            "snooze_until": self.snooze_until.isoformat() if self.snooze_until else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        """从字典创建"""
        return cls(
            id=data.get("id"),
            title=data.get("title", ""),
            description=data.get("description", ""),
            start_time=datetime.fromisoformat(data["start_time"]) if data.get("start_time") else None,
            due_time=datetime.fromisoformat(data["due_time"]) if data.get("due_time") else None,
            remind_time=datetime.fromisoformat(data["remind_time"]) if data.get("remind_time") else None,
            status=TaskStatus(data.get("status", 0)),
            tags=data.get("tags", "").split(",") if data.get("tags") else [],
            recurring_id=data.get("recurring_id"),
            notified=bool(data.get("notified", 0)),
            snooze_until=datetime.fromisoformat(data["snooze_until"]) if data.get("snooze_until") else None,
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None,
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
        )
