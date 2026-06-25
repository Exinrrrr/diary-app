-- 日记元数据表
CREATE TABLE IF NOT EXISTS entries (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    date            TEXT NOT NULL UNIQUE,          -- '2026-06-22'
    title           TEXT DEFAULT '',
    word_count      INTEGER DEFAULT 0,
    has_photos      INTEGER DEFAULT 0,
    mood            TEXT DEFAULT '',
    created_at      TEXT DEFAULT (datetime('now','localtime')),
    updated_at      TEXT DEFAULT (datetime('now','localtime'))
);

-- 照片表
CREATE TABLE IF NOT EXISTS photos (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_id        INTEGER NOT NULL,
    filename        TEXT NOT NULL,                  -- UUID 文件名
    thumb_filename  TEXT NOT NULL,                  -- 缩略图文件名
    original_name   TEXT NOT NULL,                  -- 原始上传文件名
    caption         TEXT DEFAULT '',
    sort_order      INTEGER DEFAULT 0,
    created_at      TEXT DEFAULT (datetime('now','localtime')),
    FOREIGN KEY (entry_id) REFERENCES entries(id) ON DELETE CASCADE
);

-- 提醒表
CREATE TABLE IF NOT EXISTS reminders (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    title           TEXT NOT NULL,
    description     TEXT DEFAULT '',
    remind_at       TEXT NOT NULL,                  -- ISO datetime
    entry_date      TEXT,                           -- 关联的日记日期
    is_recurring    INTEGER DEFAULT 0,
    recurring_rule  TEXT DEFAULT '',                -- 'daily'/'weekly'/'monthly'
    is_completed    INTEGER DEFAULT 0,
    is_dismissed    INTEGER DEFAULT 0,
    created_at      TEXT DEFAULT (datetime('now','localtime'))
);

-- 工作笔记：项目
CREATE TABLE IF NOT EXISTS projects (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,
    description     TEXT DEFAULT '',
    created_at      TEXT DEFAULT (datetime('now','localtime')),
    updated_at      TEXT DEFAULT (datetime('now','localtime'))
);

-- 工作笔记：笔记
CREATE TABLE IF NOT EXISTS notes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id      INTEGER NOT NULL,
    title           TEXT DEFAULT '',
    content_md      TEXT DEFAULT '',
    created_at      TEXT DEFAULT (datetime('now','localtime')),
    updated_at      TEXT DEFAULT (datetime('now','localtime')),
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_entries_date ON entries(date);
CREATE INDEX IF NOT EXISTS idx_reminders_remind_at ON reminders(remind_at);
CREATE INDEX IF NOT EXISTS idx_photos_entry ON photos(entry_id);
CREATE INDEX IF NOT EXISTS idx_notes_project ON notes(project_id);
