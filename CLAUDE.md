# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

基于 **Eel** 的任务管理器，Python 后端 + Web 前端（HTML/CSS/JS）+ SQLite 存储。

**核心特性：**
- 三种任务类型：普通任务、循环任务、常驻任务
- 任务提醒（Tkinter 强制置顶窗口）
- 全局快捷键 `Ctrl+Alt+0` 快速新建任务
- 仅在交易日触发提醒和生成循环任务

## 运行应用

```bash
uv run main_eel.py
# 或隐藏窗口启动（Windows）
run_task_manager_hidden.bat
```

## 架构

```
main_eel.py          # 入口：Eel 启动、定时任务、快捷键
api/exposed_api.py   # @eel.expose 装饰的 API 接口
api/converters.py    # 模型 → 字典 序列化
services/            # 业务逻辑层
database/manager.py  # SQLite 操作封装
models/              # 数据模型（dataclass）
ui/web/              # 前端（HTML/CSS/JS）
ui/reminder_window.py # Tkinter 提醒窗口
```

### 前后端通信

```python
# Python → JS
eel.onServicesReady()
eel.reloadTasks()
```

```javascript
// JS → Python
await eel.get_all_tasks()()
await eel.create_task(taskData)()
```

## 关键业务逻辑

### 循环任务生成
- `RecurringTaskService.process_all_recurring_tasks()` 每小时执行
- `should_generate_today()` 判断是否生成：检查交易日 + 循环规则
  - weekly：`recur_days` 存 0-6（对应 Python `weekday()`，0=周一）
  - monthly：`recur_days` 存 1-31（日期）；**必须设置 recur_days**
- 每日只生成一次实例，`last_generated_date` 防重复

### 提醒系统
- `ReminderService.trigger_reminders()` 每 60 秒执行，**仅交易日有效**
- 触发条件：`notified=False`，`snooze_until` 已过，`remind_time` 已到
- snooze 只更新 `snooze_until`，不改 `due_time` / `remind_time`

### 交易日检查 (`services/is_trade_day.py`)
- 调用腾讯金融 API，缓存整批结果到内存
- 网络失败返回 `False`；API 层捕获异常后不阻拦用户

## 数据库

```
tasks             # 普通任务（含循环任务生成的实例，recurring_id 关联）
recurring_tasks   # 循环任务定义
permanent_tasks   # 常驻任务（备忘录）
settings          # 键值对配置
```

数据库文件 `tasks.db` 不提交到 git。

## 添加新 API 接口

1. 在 [api/exposed_api.py](api/exposed_api.py) 中添加 `@eel.expose` 函数
2. 在 [ui/web/app.js](ui/web/app.js) 中调用：`await eel.函数名(参数)()`
3. 如需 UI 修改，编辑 [ui/web/index.html](ui/web/index.html) 和 [ui/web/style.css](ui/web/style.css)

## 注意事项

- 时间：Python 用 `datetime`，前端用 ISO 字符串，`converters.py` 负责转换
- 枚举：`TaskStatus`（IntEnum，0/1），`RecurType`（Enum，"daily"/"weekly"/"monthly"）
- 数据库字段名白名单：`_TASK_COLUMNS`、`_RECURRING_COLUMNS` 防 SQL 注入
- tags 在数据库以逗号分隔字符串存储，读取时 split 为列表
