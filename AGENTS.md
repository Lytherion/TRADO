# AGENTS.md

This file provides guidance for agentic coding agents working with this task manager application.

## 项目概述

这是一个基于 Eel 的现代化任务管理器，支持普通任务、循环任务和常驻任务，带 Windows 强制提醒功能。

**技术栈:**
- 后端: Python 3.10+ + Eel
- 前端: HTML/CSS/JavaScript
- 数据库: SQLite
- 架构: 三层架构 (UI层 → Service层 → Data层)

## 构建和开发命令

### 运行应用
```bash
# 主入口 - Eel 版本
python main_eel.py

# 或使用安装后的命令
task-manager
```

### 代码质量检查
```bash
# 代码格式化
black .

# 类型检查
mypy .

# 运行性能测试
python test_performance.py
```

### 测试命令
```bash
# 运行所有测试 (使用 pytest)
pytest

# 运行单个测试文件
pytest test_performance.py

# 运行特定测试函数
pytest test_performance.py::test_database_init

# 显示测试覆盖率
pytest --cov=. --cov-report=html
```

### 依赖管理
```bash
# 安装项目依赖
pip install -e .

# 安装开发依赖
pip install -e ".[dev]"

# 创建虚拟环境
python -m venv .venv
.venv\Scripts\activate  # Windows
```

## 代码风格指南

### Python 代码规范

#### 导入顺序
```python
# 标准库导入
import sys
import os
from datetime import datetime
from typing import List, Optional

# 第三方库导入
import eel

# 本地模块导入
from database.manager import DatabaseManager
from models.task import Task
from services.task_service import TaskService
```

#### 命名约定
- **类名**: PascalCase (例: `TaskService`, `DatabaseManager`)
- **函数/方法名**: snake_case (例: `create_task`, `get_all_tasks`)
- **变量名**: snake_case (例: `task_id`, `db_manager`)
- **常量**: UPPER_SNAKE_CASE (例: `DB_PATH`, `DEFAULT_TIMEOUT`)
- **私有方法**: 以下划线开头 (例: `_init_database`)

#### 类型注解
```python
from typing import List, Optional, Dict, Any
from datetime import datetime

def create_task(self, task: Task) -> int:
    """创建任务，返回任务ID"""
    pass

def get_tasks_by_status(self, status: TaskStatus) -> List[Task]:
    """根据状态获取任务列表"""
    pass
```

#### 错误处理
- 遵循"满足基本使用，规避大部分问题"原则
- 使用简单的异常处理，无需过度复杂
- 数据库操作使用上下文管理器确保连接关闭

```python
def get_task(self, task_id: int) -> Optional[Task]:
    try:
        task_dict = self.db.get_task(task_id)
        return Task.from_dict(task_dict) if task_dict else None
    except Exception as e:
        print(f"获取任务失败: {e}")
        return None
```

#### 文档字符串
```python
def create_task(self, task: Task) -> int:
    """创建新任务
    
    Args:
        task: 任务对象
        
    Returns:
        创建的任务ID
    """
    pass
```

### JavaScript 代码规范

#### 命名约定
- **变量/函数**: camelCase (例: `taskService`, `createTask`)
- **常量**: UPPER_SNAKE_CASE (例: `MAX_RETRY_COUNT`)
- **类名**: PascalCase (例: `TaskManager`)

#### 代码组织
```javascript
// ===== 全局状态 =====
const state = {
    tasks: [],
    currentFilter: 'all'
};

// ===== 工具函数 =====
function formatDate(date) {
    return date.toLocaleDateString();
}

// ===== API 调用 =====
async function createTask(taskData) {
    try {
        return await eel.create_task(taskData)();
    } catch (error) {
        console.error('创建任务失败:', error);
    }
}

// ===== 事件处理 =====
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    loadTasks();
});
```

## 架构设计

### 三层架构
```
┌─────────────────┐
│  UI Layer       │  ui/web/ (HTML/CSS/JS)
│  Eel Frontend   │  前端界面与用户交互
└────────┬────────┘
         │ eel.expose
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
- **Python → JavaScript**: 使用 `eel.expose` 暴露 Python 函数
- **JavaScript → Python**: 使用 `eel.function_name()()` 调用 Python 函数

### 核心模块
- **models/**: 数据模型 (Task, RecurringTask, PermanentTask)
- **services/**: 业务逻辑服务层
- **database/**: 数据库访问层
- **api/**: 前后端 API 接口
- **ui/**: 用户界面 (Eel 主窗口 + Web 前端)

## 数据库约定

### 表结构
- `tasks`: 普通任务
- `recurring_tasks`: 循环任务
- `permanent_tasks`: 常驻任务(备忘录)

### 时间处理
- Python 使用 `datetime` 对象
- 前端使用 ISO 格式字符串
- API 层负责格式转换

### 状态管理
- 使用枚举类型管理状态 (TaskStatus: TODO=0, COMPLETED=1)
- 循环类型使用字符串枚举 (DAILY, WEEKLY, MONTHLY)

## 开发注意事项

1. **性能优化**: 
   - 数据库查询使用索引
   - 避免频繁的数据库连接
   - 前端使用防抖处理用户输入

2. **时间处理**:
   - 统一使用 UTC 时间
   - 前端显示时转换为本地时间
   - 注意时区转换

3. **错误处理**:
   - 保持简单，避免过度复杂的异常处理
   - 关键操作添加日志记录
   - 用户友好的错误提示

4. **代码组织**:
   - 每个模块职责单一
   - 避免循环依赖
   - 使用依赖注入

5. **测试**:
   - 性能测试使用 `test_performance.py`
   - 单元测试使用 pytest
   - 集成测试覆盖主要业务流程

## 常见开发任务

### 添加新功能
1. 在 `models/` 中定义数据模型
2. 在 `services/` 中实现业务逻辑
3. 在 `api/` 中暴露 API 接口
4. 在 `ui/web/` 中实现前端界面

### 修改数据库
1. 更新 `database/schema.sql`
2. 更新相应的模型类
3. 更新 DatabaseManager 方法
4. 考虑数据迁移脚本

### 调试技巧
- 使用浏览器开发者工具调试前端
- Python 代码使用 print 语句调试
- 检查 Eel 控制台输出
- 查看 SQLite 数据库内容