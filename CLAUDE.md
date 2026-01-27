# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

这是一个任务管理器应用,使用 PyWebView 作为 UI 层,Python 作为业务逻辑层,SQLite 作为数据存储。

**核心特性:**
- 支持三种任务类型:普通任务、循环任务、常驻任务
- 提供任务提醒功能
- 使用 Web 技术(HTML/CSS/JavaScript)构建现代化 UI
- Python 后端处理所有业务逻辑

## 开发环境

### 运行应用
```bash
# 运行 PyWebView 版本(当前主版本)
python main_webview.py

# 或使用已安装的命令
task-manager
```

### 依赖管理
```bash
# 激活虚拟环境(如果使用)
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # macOS/Linux

# 安装依赖
pip install -e .
```

## 架构设计

### 三层架构

```
┌─────────────────┐
│  UI Layer       │  ui/web/ (HTML/CSS/JS)
│  PyWebView      │  前端界面与用户交互
└────────┬────────┘
         │ window.pywebview.api
┌────────┴────────┐
│  Service Layer  │  services/ (Python)
│  业务逻辑       │  TaskService, RecurringTaskService等
└────────┬────────┘
         │
┌────────┴────────┐
│  Data Layer     │  database/ + models/
│  数据库访问     │  DatabaseManager + SQLite
└─────────────────┘
```

### 前后端通信

**Python → JavaScript:**
```python
# 在 Python 中调用前端 JS 函数
self.window.evaluate_js('showReminderDialog(1, "任务标题")')
```

**JavaScript → Python:**
```javascript
// 前端调用 Python API
const tasks = await window.pywebview.api.get_all_tasks();
await window.pywebview.api.create_task(taskData);
```

## 核心模块说明

### 1. WebAPI 类 (main_webview.py)
- 暴露给前端的所有 API 接口
- 负责数据格式转换(Python 对象 ↔ JSON)
- 所有前端请求都通过这个类处理

### 2. 服务层 (services/)
- **TaskService**: 普通任务的 CRUD 和状态管理
- **RecurringTaskService**: 循环任务管理,自动生成任务实例
- **PermanentTaskService**: 常驻任务(备忘录)管理
- **ReminderService**: 定时检查并触发任务提醒

### 3. 数据模型 (models/)
- **Task**: 普通任务模型
- **RecurringTask**: 循环任务模型
- **PermanentTask**: 常驻任务模型
- **TaskStatus**: 任务状态枚举(TODO=0, COMPLETED=1)
- **RecurType**: 循环类型枚举(DAILY, WEEKLY, MONTHLY)

### 4. 数据库层 (database/)
- **DatabaseManager**: 数据库操作的统一入口
- **schema.sql**: 数据库表结构定义
- 使用 SQLite,数据库文件位于 `tasks.db`

### 5. 前端代码 (ui/web/)
- **index.html**: UI 结构
- **style.css**: 样式定义
- **app.js**: 前端逻辑、API 调用、事件处理

## 数据库表结构

### tasks (普通任务)
- 基本字段: id, title, description
- 时间字段: due_time, remind_time, created_at, completed_at
- 状态字段: status (0=未完成, 1=已完成)
- 关联字段: recurring_id (关联循环任务)
- 提醒字段: notified, snooze_until

### recurring_tasks (循环任务)
- 基本字段: id, title, description, remind_time
- 循环规则: recur_type, recur_days, recur_end_date
- 实例管理: last_generated_date, next_generate_date
- 状态字段: is_active

### permanent_tasks (常驻任务)
- 简单的备忘录,只包含 title, description, tags

## 关键业务逻辑

### 循环任务生成机制
- RecurringTaskService 负责根据循环规则自动生成普通任务实例
- 生成的任务实例通过 `recurring_id` 字段关联到循环任务
- 每天自动检查是否需要生成新的任务实例

### 任务提醒系统
- ReminderService 定时检查所有未提醒的任务
- 当到达 remind_time 时触发提醒回调
- 支持延迟提醒(snooze)功能

### 任务状态管理
- 使用 TaskStatus 枚举管理状态
- 完成任务时自动记录 completed_at 时间戳
- 修改提醒时间时自动重置 notified 标志

## 文件路径约定

- 配置文件: `config.py` (包含数据库路径、默认配置等)
- 数据库文件: `tasks.db` (项目根目录)
- Web 资源: `ui/web/` (HTML/CSS/JS)
- SQL Schema: `database/schema.sql`

## 常见开发任务

### 添加新的 API 接口
1. 在 `WebAPI` 类中添加新方法
2. 在 `ui/web/app.js` 中调用新 API
3. 如需 UI 更新,修改 `index.html` 和 `style.css`

### 修改数据库表结构
1. 更新 `database/schema.sql`
2. 更新相应的模型类(models/)
3. 更新 DatabaseManager 中的相关方法
4. 考虑数据迁移(如果需要)

### 修改前端 UI
- 直接编辑 `ui/web/` 下的文件
- 重启应用即可看到效果
- 可使用浏览器开发者工具调试

## 注意事项

1. **时间处理**:
   - Python 使用 datetime 对象
   - 前端使用 ISO 格式字符串
   - WebAPI 负责格式转换

2. **数据库连接**:
   - 使用上下文管理器确保连接正确关闭
   - 所有数据库操作通过 DatabaseManager

3. **枚举类型**:
   - TaskStatus 是 IntEnum (存储为整数)
   - RecurType 是 Enum (存储为字符串)

4. **前端异步**:
   - 所有 Python API 调用都是异步的
   - 使用 async/await 处理

5. **错误处理**:
   - 代码遵循"满足基本使用规避大部分问题"原则
   - 无需过度复杂的异常处理
