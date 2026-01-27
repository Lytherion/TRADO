# 任务管理器 - Eel 版本

基于 Eel 框架的现代化任务管理器,支持普通任务、循环任务和常驻任务,带 Windows 原生强制提醒功能。

## 特性

### 核心功能
- ✅ **普通任务**: 带截止时间和提醒的一次性任务
- ✅ **循环任务**: 每日/每周/每月自动生成的重复任务
- ✅ **常驻任务**: 长期备忘录,无截止时间
- ✅ **强制提醒**: Windows MessageBox 原生弹窗,自动置顶前台
- ✅ **双重通知**: 系统弹窗 + Web 界面同时提醒

### 技术特点
- 使用 Eel 框架,比 PyWebView 更稳定可靠
- 浏览器渲染界面,现代化 UI
- SQLite 数据库,轻量高效
- 后台线程处理,不阻塞界面
- WAL 模式提升数据库并发性能

## 技术架构

```
┌─────────────────────────────────────┐
│       前端 (Web Browser)           │
│  ┌──────────────────────────────┐  │
│  │   HTML/CSS/JS                │  │
│  │   - index.html (结构)        │  │
│  │   - style.css (样式)         │  │
│  │   - app.js (逻辑)            │  │
│  └──────────────────────────────┘  │
└─────────────┬───────────────────────┘
              │ eel.xxx()()
              │
┌─────────────┴───────────────────────┐
│      后端 (Python + Eel)            │
│  ┌──────────────────────────────┐  │
│  │   @eel.expose API 函数       │  │
│  │   - 17 个暴露给前端的接口    │  │
│  └──────────────────────────────┘  │
│  ┌──────────────────────────────┐  │
│  │   Windows 原生弹窗           │  │
│  │   - MessageBox API           │  │
│  │   - 自动置顶前台             │  │
│  └──────────────────────────────┘  │
│  ┌──────────────────────────────┐  │
│  │   业务逻辑服务               │  │
│  │   - TaskService              │  │
│  │   - RecurringTaskService     │  │
│  │   - PermanentTaskService     │  │
│  │   - ReminderService          │  │
│  └──────────────────────────────┘  │
│  ┌──────────────────────────────┐  │
│  │   数据层                     │  │
│  │   - DatabaseManager          │  │
│  │   - SQLite (WAL 模式)        │  │
│  └──────────────────────────────┘  │
└─────────────────────────────────────┘
```

## 安装

### 依赖要求
- Python >= 3.10
- Eel >= 0.16.0

### 安装步骤

```bash
# 1. 克隆项目
git clone <repository-url>
cd task_manager_qt

# 2. 安装依赖
pip install eel>=0.16.0

# 3. 运行应用
python main_eel.py
```

## 使用说明

### 普通任务
1. 点击 "➕ 新建任务" 按钮
2. 填写任务标题、描述、截止时间、提醒时间
3. 可选添加标签
4. 保存后任务会出现在列表中
5. 到达提醒时间会弹出 Windows 系统弹窗和 Web 界面提醒

### 循环任务
1. 切换到 "🔄 循环任务" 标签
2. 点击 "➕ 新建循环任务"
3. 设置循环类型:
   - **每日**: 每天生成任务
   - **每周**: 指定星期几生成任务
   - **每月**: 指定日期生成任务
4. 系统每小时自动检查并生成新任务实例

### 常驻任务
1. 切换到 "📌 常驻任务" 标签
2. 点击 "➕ 新建常驻任务"
3. 添加长期备忘事项
4. 常驻任务无截止时间,始终显示

### 提醒功能
- **双重提醒**: 到达提醒时间时:
  1. Windows MessageBox 系统弹窗 (自动置顶前台,强制关注)
  2. Web 界面提醒对话框
- **操作选项**:
  - 完成任务: 标记任务为已完成
  - 延迟提醒: 5/10/30 分钟后再次提醒
  - 关闭: 仅关闭提醒对话框

## 项目结构

```
task_manager_qt/
├── main_eel.py              # Eel 应用入口
├── config.py                # 配置文件
├── models/                  # 数据模型
│   ├── task.py             # 普通任务模型
│   ├── recurring_task.py   # 循环任务模型
│   ├── permanent_task.py   # 常驻任务模型
│   └── enums.py            # 枚举类型
├── database/                # 数据库层
│   ├── manager.py          # 数据库管理器
│   └── schema.sql          # 数据库表结构
├── services/                # 业务逻辑层
│   ├── task_service.py     # 任务服务
│   ├── recurring_service.py # 循环任务服务
│   ├── permanent_task_service.py # 常驻任务服务
│   └── reminder_service.py # 提醒服务
└── ui/web/                  # Web 前端
    ├── index.html          # HTML 结构
    ├── style.css           # CSS 样式
    └── app.js              # JavaScript 逻辑
```

## API 接口

### 任务管理 (7 个)
- `get_all_tasks()` - 获取所有任务
- `get_today_tasks()` - 获取今日任务
- `get_task(task_id)` - 获取单个任务
- `create_task(task_data)` - 创建任务
- `update_task(task_id, task_data)` - 更新任务
- `delete_task(task_id)` - 删除任务
- `toggle_task_status(task_id)` - 切换任务状态

### 循环任务 (4 个)
- `get_all_recurring_tasks()` - 获取所有循环任务
- `create_recurring_task(task_data)` - 创建循环任务
- `update_recurring_task(task_id, task_data)` - 更新循环任务
- `delete_recurring_task(task_id)` - 删除循环任务

### 常驻任务 (4 个)
- `get_all_permanent_tasks()` - 获取所有常驻任务
- `create_permanent_task(task_data)` - 创建常驻任务
- `update_permanent_task(task_id, task_data)` - 更新常驻任务
- `delete_permanent_task(task_id)` - 删除常驻任务

### 提醒功能 (2 个)
- `snooze_reminder(task_id, minutes)` - 延迟提醒
- `dismiss_reminder()` - 关闭提醒

## 开发说明

### 性能测试
运行性能测试脚本检查初始化时间:
```bash
python test_performance.py
```

### 数据库
- 使用 SQLite WAL 模式提高并发性能
- 自动创建索引优化查询
- 支持多线程访问

### 定时任务
- **循环任务处理**: 每小时检查一次
- **提醒检查**: 每 60 秒检查一次
- 所有定时任务在后台线程执行,不阻塞界面

## 常见问题

### 提醒不弹出?
- 确保任务设置了提醒时间
- 检查系统时间是否正确
- Windows 弹窗会自动置顶,即使应用在后台

### 应用无响应?
- Eel 版本已解决 PyWebView 的阻塞问题
- 所有耗时操作都在后台线程执行
- 如遇问题请查看控制台日志

### 如何打包成可执行文件?
```bash
pip install pyinstaller
pyinstaller --onefile --windowed main_eel.py
```

## License

MIT License

## 更新日志

### v2.0.0 (2024-01-20)
- 从 PyWebView 迁移到 Eel 框架
- 新增 Windows 原生强制提醒弹窗
- 优化数据库并发性能 (WAL 模式)
- 所有操作改为后台线程执行
- 修复界面无响应问题
