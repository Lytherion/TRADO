# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

基于 PySide6 的现代化任务管理应用,支持两种任务类型:
- **普通任务**: 标准的待办事项,支持提醒、标签等
- **循环任务**: 每日/每周/每月重复任务,自动生成实例
- **常驻任务**: 备忘录式长期任务,无截止日期和状态,用于保存重要笔记和想法

## 常用命令

```bash
# 安装依赖
pip install -e .

# 运行应用
python main.py

# 或者安装后直接运行
task-manager

# 开发工具(可选)
pip install -e ".[dev]"
black .              # 代码格式化
mypy .               # 类型检查
```

## 核心架构

### 应用入口与服务注册

[main.py](main.py) 是应用入口,采用**服务注入模式**:
1. 初始化 `DatabaseManager` (SQLite)
2. 创建三个核心服务: `TaskService`, `RecurringTaskService`, `PermanentTaskService`
3. 创建 `ReminderService` 并设置回调
4. 将所有服务注入到 `MainWindow`

### 数据层设计

- **DatabaseManager** ([database/manager.py](database/manager.py)): 封装所有 SQL 操作,提供 CRUD 接口
- **Schema** ([database/schema.sql](database/schema.sql)): 3个表设计
  - `tasks`: 所有任务实例(包括普通任务和循环任务生成的实例)
  - `recurring_tasks`: 循环任务模板
  - `permanent_tasks`: 常驻任务(备忘录)
  - `settings`: 应用配置

**关键关联**:
- 循环任务通过 `recurring_id` 关联到生成的任务实例

### 业务逻辑层

**Services 职责划分**:

1. **TaskService**: 管理所有任务实例(普通任务 + 循环任务生成的实例)
   - CRUD 操作
   - 状态管理(未完成/已完成)
   - 筛选查询(今日任务、本周任务等)

2. **RecurringTaskService**: 循环任务管理
   - **核心机制**: 每天午夜自动生成当日实例,销毁前一天的旧实例
   - 支持 daily/weekly/monthly 三种循环类型
   - `should_generate_today()`: 判断是否应为某日生成实例
   - `generate_task_instances()`: 批量生成实例
   - `cleanup_old_instances()`: 清理旧实例

3. **PermanentTaskService**: 常驻任务管理
   - 管理备忘录式长期任务
   - CRUD 操作和标签管理
   - 不涉及状态变更,仅用于信息存储

4. **ReminderService**: 提醒系统
   - 每分钟检查到期任务(通过 Qt 定时器)
   - 支持 Snooze 延迟提醒
   - 回调模式触发 UI 弹窗

### UI 层设计

**主窗口架构** ([ui/main_window.py](ui/main_window.py)):
- 左侧边栏: 任务视图切换(所有任务/今日任务/循环任务/常驻任务)
- 中间区域: 任务列表,按 remind_time 排序(无提醒时间的排在最后),支持分组显示(未完成/已完成)
- 顶部工具栏: 新建任务/循环任务/常驻任务按钮
- 双击任务项可直接编辑

**对话框**:
- `TaskDialog`: 创建/编辑普通任务
- `RecurringDialog`: 创建循环任务,选择循环类型和重复日期
- `PermanentTaskDialog`: 创建/编辑常驻任务
- `ReminderWidget`: **模态提醒弹窗**,用户必须处理,支持完成/延迟/忽略操作

**系统托盘** ([ui/tray_icon.py](ui/tray_icon.py)):
- 最小化到托盘常驻后台
- 托盘通知提醒

## 数据模型

定义在 [models/enums.py](models/enums.py) 和 [models/](models/) 目录:

**枚举类型**:
- `TaskStatus`: 未完成(0)/已完成(1)
- `RecurType`: daily/weekly/monthly

**数据模型**:
- `Task` ([models/task.py](models/task.py)): 普通任务数据模型
- `RecurringTask` ([models/recurring_task.py](models/recurring_task.py)): 循环任务数据模型
- `PermanentTask` ([models/permanent_task.py](models/permanent_task.py)): 常驻任务数据模型(备忘录)

## 配置管理

[config.py](config.py) 定义:
- `DB_PATH`: 数据库路径 (tasks.db)
- `DEFAULT_CONFIG`: 提醒检查间隔(60秒)、延迟时长(10分钟)、清理时间(午夜)
- `STATUS_COLORS`: 状态颜色映射

## 关键实现细节

### 循环任务实例生成机制

1. 循环任务保存在 `recurring_tasks` 表作为模板
2. 每天午夜检查所有活跃的循环任务
3. 根据 `recur_type` 和 `recur_days` 判断是否应为今日生成
4. 生成的任务实例保存在 `tasks` 表,带 `recurring_id` 外键
5. 同时删除前一天的旧实例(无论是否完成)

### 任务排序机制

任务列表按以下规则排序:
1. 按 `remind_time` 升序排列(提醒时间越近越靠前)
2. 无 `remind_time` 的任务排在列表最后(使用 `datetime.max` 作为排序键)
3. 同一分类(未完成/已完成)内独立排序

**实现**:
```python
tasks.sort(key=lambda t: t.remind_time if t.remind_time else datetime.max)
```

### 提醒检查流程

1. Qt 定时器每 60 秒调用 `ReminderService.trigger_reminders()`
2. 检查所有未完成任务的 `remind_time`
3. 跳过已提醒(`notified=1`)或 Snooze 中的任务
4. 触发回调显示 `ReminderWidget` **模态弹窗**
5. 用户必须处理提醒:
   - 完成任务: 标记完成并刷新任务列表
   - Snooze X 分钟: 延迟提醒
   - 忽略: 关闭弹窗但不做处理

## 数据库文件位置

- 默认: 项目根目录 `tasks.db`
- 自动创建,包含完整 schema 和索引

## 样式文件

[ui/styles.qss](ui/styles.qss) - Qt 样式表,定义现代化 UI 外观
