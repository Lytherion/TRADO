"""
常驻任务(备忘录)数据模型
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class PermanentTask:
    """常驻任务"""

    id: Optional[int] = None
    title: str = ""
    description: str = ""
    tags: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        """转为字典"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "tags": self.tags,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PermanentTask":
        """从字典创建"""
        task = cls()
        task.id = data.get("id")
        task.title = data.get("title", "")
        task.description = data.get("description", "")
        task.tags = data.get("tags", "")

        created_at = data.get("created_at")
        if created_at:
            task.created_at = datetime.fromisoformat(created_at)

        updated_at = data.get("updated_at")
        if updated_at:
            task.updated_at = datetime.fromisoformat(updated_at)

        return task
