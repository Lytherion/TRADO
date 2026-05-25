-- 普通任务表
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- 基本信息
    title TEXT NOT NULL,
    description TEXT,

    -- 时间
    start_time TEXT,
    remind_time TEXT,       -- 下次弹窗时间，延后后直接更新此字段

    -- 属性
    status INTEGER DEFAULT 0,
    tags TEXT,

    -- 关联
    recurring_id INTEGER,

    -- 提醒
    notified INTEGER DEFAULT 0,

    -- 元数据
    created_at TEXT NOT NULL,
    updated_at TEXT,
    completed_at TEXT,

    FOREIGN KEY (recurring_id) REFERENCES recurring_tasks(id) ON DELETE CASCADE
);

-- 循环任务表
CREATE TABLE IF NOT EXISTS recurring_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- 基本信息
    title TEXT NOT NULL,
    description TEXT,
    remind_time TEXT NOT NULL,

    -- 属性
    tags TEXT,

    -- 循环规则
    recur_type TEXT NOT NULL,
    recur_interval INTEGER DEFAULT 1,
    recur_days TEXT,
    recur_end_date TEXT,

    -- 实例管理
    last_generated_date TEXT,
    next_generate_date TEXT,

    -- 其他
    is_active INTEGER DEFAULT 1,
    created_at TEXT NOT NULL
);

-- 常驻任务表(备忘录)
CREATE TABLE IF NOT EXISTS permanent_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- 基本信息
    title TEXT NOT NULL,
    description TEXT,

    -- 属性
    tags TEXT,

    -- 元数据
    created_at TEXT NOT NULL,
    updated_at TEXT
);

-- 配置表
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_remind_time ON tasks(remind_time);
CREATE INDEX IF NOT EXISTS idx_tasks_recurring_id ON tasks(recurring_id);
CREATE INDEX IF NOT EXISTS idx_recurring_active ON recurring_tasks(is_active);
