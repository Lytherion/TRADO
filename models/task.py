from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from .enums import TaskStatus


@dataclass
class Task:
    title: str = ""
    description: str = ""

    start_time: Optional[datetime] = None
    remind_time: Optional[datetime] = None  # 下次弹窗时间，延后后直接更新此字段

    status: TaskStatus = TaskStatus.TODO
    tags: List[str] = field(default_factory=list)

    id: Optional[int] = None
    recurring_id: Optional[int] = None

    notified: bool = False

    created_at: datetime = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "remind_time": self.remind_time.isoformat() if self.remind_time else None,
            "status": self.status.value,
            "tags": ",".join(self.tags) if self.tags else "",
            "recurring_id": self.recurring_id,
            "notified": 1 if self.notified else 0,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        return cls(
            id=data.get("id"),
            title=data.get("title", ""),
            description=data.get("description", ""),
            start_time=datetime.fromisoformat(data["start_time"]) if data.get("start_time") else None,
            remind_time=datetime.fromisoformat(data["remind_time"]) if data.get("remind_time") else None,
            status=TaskStatus(data.get("status", 0)),
            tags=data.get("tags", "").split(",") if data.get("tags") else [],
            recurring_id=data.get("recurring_id"),
            notified=bool(data.get("notified", 0)),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None,
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
        )
