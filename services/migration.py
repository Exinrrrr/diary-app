"""将旧的 北京实习日记.md 迁移到新系统"""

import os
import re
from typing import Optional, List, Dict
from database.db import get_db
from config import ENTRIES_DIR


def parse_date_from_heading(heading: str, default_year: int = 2026) -> Optional[str]:
    """从标题中提取日期，如 '第一天（6月16日）' → '2026-06-16'"""
    match = re.search(r'(\d{1,2})月(\d{1,2})日', heading)
    if match:
        month = int(match.group(1))
        day = int(match.group(2))
        return f'{default_year}-{month:02d}-{day:02d}'
    return None


def parse_title_from_heading(heading: str) -> str:
    """从标题中提取描述，如 '第一天（6月16日）—— 抵达北京' → '抵达北京'"""
    # 去掉日期部分
    title = re.sub(r'第[一二三四五六七八九十\d]+天\s*（\d{1,2}月\d{1,2}日）', '', heading)
    # 去掉 —— 和多余符号
    title = re.sub(r'^[——\-—\s]+', '', title)
    return title.strip()


def parse_existing_diary(filepath: str) -> List[Dict]:
    """
    解析旧日记文件，返回条目列表。
    每个条目: {date, title, content_md}
    """
    if not os.path.exists(filepath):
        return []

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 按 --- 分割各天
    sections = content.split('\n---\n')

    entries = []
    for section in sections:
        section = section.strip()
        if not section:
            continue

        lines = section.split('\n')
        if not lines:
            continue

        # 找标题行（以 ## 开头）
        heading = ''
        content_lines = []
        found_heading = False

        for line in lines:
            stripped = line.strip()
            if not found_heading and stripped.startswith('## '):
                heading = stripped[3:]  # 去掉 '## '
                found_heading = True
            elif found_heading:
                content_lines.append(line)

        if not heading:
            continue

        date_str = parse_date_from_heading(heading)
        if not date_str:
            continue

        title = parse_title_from_heading(heading)
        content_md = '\n'.join(content_lines).strip()

        # 清理内容：去掉开头的引用行（如 '> 2026年6月...'）
        content_md = re.sub(r'^>.*\n?', '', content_md).strip()

        entries.append({
            'date': date_str,
            'title': title,
            'content_md': content_md,
        })

    return entries


def migrate_existing_diary(source_path: str) -> dict:
    """
    执行迁移：读取旧日记 → 写入独立 .md 文件 → 插入数据库。
    返回: {imported: int, skipped: int, errors: list}
    """
    entries = parse_existing_diary(source_path)

    if not entries:
        return {'imported': 0, 'skipped': 0, 'errors': ['没有找到可导入的日记条目']}

    db = get_db()
    imported = 0
    skipped = 0
    errors = []

    for entry in entries:
        date_str = entry['date']
        title = entry['title']
        content_md = entry['content_md']

        # 检查是否已存在
        existing = db.execute(
            "SELECT id FROM entries WHERE date = ?", (date_str,)
        ).fetchone()

        if existing:
            skipped += 1
            continue

        try:
            # 写入 markdown 文件
            md_path = os.path.join(ENTRIES_DIR, f'{date_str}.md')
            full_content = f'# {title}\n\n{content_md}' if title else content_md
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(full_content)

            # 插入数据库
            word_count = len(content_md)
            db.execute(
                """INSERT INTO entries (date, title, word_count)
                   VALUES (?, ?, ?)""",
                (date_str, title, word_count)
            )

            imported += 1
        except Exception as e:
            errors.append(f'{date_str}: {str(e)}')

    db.commit()

    return {
        'imported': imported,
        'skipped': skipped,
        'errors': errors,
    }
