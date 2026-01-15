"""
配置文件
"""
from pathlib import Path

# 项目根目录
BASE_DIR = Path(__file__).parent

# 数据库文件路径
DB_PATH = BASE_DIR / "tasks.db"

# 默认配置
DEFAULT_CONFIG = {
    "theme": "light",  # light/dark
    "window_size": (1000, 700),
    "reminder_check_interval": 60000,  # 毫秒，60秒检查一次
    "snooze_duration": 10,  # 延迟提醒分钟数
    "auto_cleanup_time": "00:00",  # 循环任务自动清理时间
}

# 状态颜色
STATUS_COLORS = {
    0: "#6b7280",  # 待办 - 灰色
    1: "#3b82f6",  # 进行中 - 蓝色
    2: "#10b981",  # 已完成 - 绿色
    3: "#ef4444",  # 已取消 - 红色
}
