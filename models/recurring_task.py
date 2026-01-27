"""
循环任务模型
"""
from dataclasses import dataclass, field
from datetime import datetime, date, time
from typing import Optional, List
from .enums import RecurType


@dataclass
class RecurringTask:
    """循环任务"""

    # 基本信息
    title: str = ""
    description: str = ""
    remind_time: time = field(default_factory=lambda: time(9, 0))

    # 属性
    tags: List[str] = field(default_factory=list)

    # 循环规则
    recur_type: RecurType = RecurType.daily
    recur_interval: int = 1  # 间隔数
    recur_days: List[int] = field(default_factory=list)  # 每周哪几天 [0-6]
    recur_end_date: Optional[date] = None

    # 实例管理
    last_generated_date: Optional[date] = None
    next_generate_date: Optional[date] = None

    # 其他
    id: Optional[int] = None
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "remind_time": self.remind_time.isoformat(),
            "tags": ",".join(self.tags) if self.tags else "",
            "recur_type": self.recur_type.value,
            "recur_interval": self.recur_interval,
            "recur_days": ",".join(map(str, self.recur_days)) if self.recur_days else "",
            "recur_end_date": self.recur_end_date.isoformat() if self.recur_end_date else None,
            "last_generated_date": self.last_generated_date.isoformat() if self.last_generated_date else None,
            "next_generate_date": self.next_generate_date.isoformat() if self.next_generate_date else None,
            "is_active": 1 if self.is_active else 0,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RecurringTask":
        """从字典创建"""
        return cls(
            id=data.get("id"),
            title=data.get("title", ""),
            description=data.get("description", ""),
            remind_time=time.fromisoformat(data.get("remind_time", "09:00:00")),
            tags=data.get("tags", "").split(",") if data.get("tags") else [],
            recur_type=RecurType(data.get("recur_type", "daily")),
            recur_interval=data.get("recur_interval", 1),
            recur_days=[int(d) for d in data.get("recur_days", "").split(",") if d],
            recur_end_date=date.fromisoformat(data["recur_end_date"]) if data.get("recur_end_date") else None,
            last_generated_date=date.fromisoformat(data["last_generated_date"]) if data.get("last_generated_date") else None,
            next_generate_date=date.fromisoformat(data["next_generate_date"]) if data.get("next_generate_date") else None,
            is_active=bool(data.get("is_active", 1)),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(),
        )
