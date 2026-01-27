# -*- coding: utf-8 -*-
"""
性能测试脚本 - 测试各个组件的初始化时间
"""
import sys
import time
from pathlib import Path

# 设置控制台输出编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 测试数据库初始化
print("=" * 50)
print("测试 1: 数据库初始化")
print("=" * 50)
start = time.time()

from config import DB_PATH
from database.manager import DatabaseManager

db_start = time.time()
db = DatabaseManager(DB_PATH)
db_time = time.time() - db_start
print(f"[OK] 数据库初始化: {db_time:.3f}秒")

# 测试服务初始化
print("\n" + "=" * 50)
print("测试 2: 服务层初始化")
print("=" * 50)

from services.task_service import TaskService
from services.recurring_service import RecurringTaskService
from services.permanent_task_service import PermanentTaskService
from services.reminder_service import ReminderService

service_start = time.time()
task_service = TaskService(db)
print(f"[OK] TaskService: {time.time() - service_start:.3f}秒")

recurring_start = time.time()
recurring_service = RecurringTaskService(db, task_service)
print(f"[OK] RecurringTaskService: {time.time() - recurring_start:.3f}秒")

permanent_start = time.time()
permanent_service = PermanentTaskService(db)
print(f"[OK] PermanentTaskService: {time.time() - permanent_start:.3f}秒")

reminder_start = time.time()
reminder_service = ReminderService(task_service)
print(f"[OK] ReminderService: {time.time() - reminder_start:.3f}秒")

# 测试数据库查询
print("\n" + "=" * 50)
print("测试 3: 数据库查询性能")
print("=" * 50)

query_start = time.time()
tasks = task_service.get_all_tasks()
print(f"[OK] 查询所有任务 ({len(tasks)}条): {time.time() - query_start:.3f}秒")

query_start = time.time()
recurring_tasks = recurring_service.get_all_recurring_tasks()
print(f"[OK] 查询循环任务 ({len(recurring_tasks)}条): {time.time() - query_start:.3f}秒")

query_start = time.time()
permanent_tasks = permanent_service.get_all_tasks()
print(f"[OK] 查询常驻任务 ({len(permanent_tasks)}条): {time.time() - query_start:.3f}秒")

# 总结
total_time = time.time() - start
print("\n" + "=" * 50)
print(f"总耗时: {total_time:.3f}秒")
print("=" * 50)

if total_time > 2.0:
    print("\n[WARNING] 总初始化时间超过 2 秒，可能导致启动卡顿")
elif total_time > 1.0:
    print("\n[INFO] 初始化时间略长，建议优化")
else:
    print("\n[OK] 性能良好")
