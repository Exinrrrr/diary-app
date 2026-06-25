"""数据库连接和初始化"""

import sqlite3
import os
from flask import g
from config import DATABASE

def get_db():
    """获取当前请求的数据库连接"""
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row  # 字典式访问
        g.db.execute("PRAGMA journal_mode=WAL")
        g.db.execute("PRAGMA foreign_keys=ON")
    return g.db

def close_db(e=None):
    """请求结束时关闭数据库"""
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    """初始化数据库（首次运行时调用）"""
    os.makedirs(os.path.dirname(DATABASE), exist_ok=True)
    db = sqlite3.connect(DATABASE)
    schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
    with open(schema_path, 'r', encoding='utf-8') as f:
        db.executescript(f.read())
    db.commit()
    db.close()
    print(f"数据库已初始化: {DATABASE}")
