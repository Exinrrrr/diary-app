"""日记 API 路由"""

import os
from flask import Blueprint, request, jsonify
from database.db import get_db
from config import ENTRIES_DIR
from services.auto_format import auto_format

entries_bp = Blueprint('entries', __name__)


def get_entry_file(date_str: str) -> str:
    """获取某一天的 markdown 文件路径"""
    return os.path.join(ENTRIES_DIR, f'{date_str}.md')


def read_entry_content(date_str: str) -> str:
    """读取日记的 markdown 内容"""
    filepath = get_entry_file(date_str)
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    return ''


def write_entry_content(date_str: str, content: str):
    """写入日记的 markdown 内容"""
    filepath = get_entry_file(date_str)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)


def entry_to_dict(row) -> dict:
    """将数据库行转为字典"""
    if not row:
        return None
    entry = dict(row)
    entry['content_md'] = read_entry_content(entry['date'])
    # 加载关联的照片
    db = get_db()
    photos = db.execute(
        "SELECT * FROM photos WHERE entry_id = ? ORDER BY sort_order",
        (entry['id'],)
    ).fetchall()
    entry['photos'] = [dict(p) for p in photos]
    entry['has_photos'] = len(entry['photos']) > 0
    return entry


@entries_bp.route('/entries', methods=['GET'])
def list_entries():
    """获取指定月份的日记列表（不含完整内容）"""
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)

    if not year or not month:
        return jsonify({'error': '缺少 year 或 month 参数'}), 400

    db = get_db()
    start_date = f'{year}-{month:02d}-01'
    if month == 12:
        end_date = f'{year + 1}-01-01'
    else:
        end_date = f'{year}-{month + 1:02d}-01'

    rows = db.execute(
        """SELECT id, date, title, word_count, has_photos, mood, updated_at
           FROM entries
           WHERE date >= ? AND date < ?
           ORDER BY date""",
        (start_date, end_date)
    ).fetchall()

    entries = []
    for row in rows:
        entry = dict(row)
        # 检查是否真的有照片
        photo_count = db.execute(
            "SELECT COUNT(*) FROM photos WHERE entry_id = ?",
            (entry['id'],)
        ).fetchone()[0]
        entry['has_photos'] = photo_count > 0
        entries.append(entry)

    return jsonify(entries)


@entries_bp.route('/entries/<date>', methods=['GET'])
def get_entry(date):
    """获取某一天的日记完整内容"""
    db = get_db()
    row = db.execute(
        "SELECT * FROM entries WHERE date = ?",
        (date,)
    ).fetchone()

    if not row:
        return jsonify(None)

    return jsonify(entry_to_dict(row))


@entries_bp.route('/entries', methods=['POST'])
def create_entry():
    """创建新日记"""
    data = request.get_json()
    if not data or 'date' not in data:
        return jsonify({'error': '缺少 date 字段'}), 400

    date = data['date']
    title = data.get('title', '')
    content_md = data.get('content_md', '')
    mood = data.get('mood', '')

    db = get_db()

    # 检查是否已存在
    existing = db.execute(
        "SELECT id FROM entries WHERE date = ?", (date,)
    ).fetchone()
    if existing:
        return jsonify({'error': '该日期已有日记'}), 409

    # 写入文件
    write_entry_content(date, content_md)

    # 插入数据库
    word_count = len(content_md)
    cursor = db.execute(
        """INSERT INTO entries (date, title, word_count, mood)
           VALUES (?, ?, ?, ?)""",
        (date, title, word_count, mood)
    )
    db.commit()

    row = db.execute("SELECT * FROM entries WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return jsonify(entry_to_dict(row)), 201


@entries_bp.route('/entries/<date>', methods=['PUT'])
def update_entry(date):
    """更新日记"""
    data = request.get_json()
    if not data:
        return jsonify({'error': '缺少请求体'}), 400

    db = get_db()
    row = db.execute("SELECT id FROM entries WHERE date = ?", (date,)).fetchone()

    if not row:
        # 不存在则创建
        return create_entry_internal(date, data)

    title = data.get('title', '')
    content_md = data.get('content_md', '')
    mood = data.get('mood', '')

    # 写入文件
    write_entry_content(date, content_md)

    # 更新数据库
    word_count = len(content_md)
    db.execute(
        """UPDATE entries
           SET title = ?, word_count = ?, mood = ?, updated_at = datetime('now','localtime')
           WHERE date = ?""",
        (title, word_count, mood, date)
    )
    db.commit()

    row = db.execute("SELECT * FROM entries WHERE date = ?", (date,)).fetchone()
    return jsonify(entry_to_dict(row))


def create_entry_internal(date, data):
    """内部创建日记（PUT 时自动创建）"""
    db = get_db()
    title = data.get('title', '')
    content_md = data.get('content_md', '')
    mood = data.get('mood', '')

    write_entry_content(date, content_md)

    word_count = len(content_md)
    cursor = db.execute(
        """INSERT INTO entries (date, title, word_count, mood)
           VALUES (?, ?, ?, ?)""",
        (date, title, word_count, mood)
    )
    db.commit()
    row = db.execute("SELECT * FROM entries WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return jsonify(entry_to_dict(row)), 201


@entries_bp.route('/entries/<date>', methods=['DELETE'])
def delete_entry(date):
    """删除日记（含关联照片和文件）"""
    db = get_db()
    row = db.execute("SELECT id FROM entries WHERE date = ?", (date,)).fetchone()

    if not row:
        return jsonify({'error': '日记不存在'}), 404

    entry_id = row['id']

    # 删除关联照片文件
    photos = db.execute("SELECT * FROM photos WHERE entry_id = ?", (entry_id,)).fetchall()
    for photo in photos:
        from config import PHOTOS_DIR
        photo_dir = os.path.join(PHOTOS_DIR, date)
        filepath = os.path.join(photo_dir, photo['filename'])
        thumb_path = os.path.join(photo_dir, photo['thumb_filename'])
        for p in [filepath, thumb_path]:
            if os.path.exists(p):
                os.remove(p)

    # 删除数据库记录
    db.execute("DELETE FROM photos WHERE entry_id = ?", (entry_id,))
    db.execute("DELETE FROM entries WHERE id = ?", (entry_id,))
    db.commit()

    # 删除 markdown 文件
    md_path = get_entry_file(date)
    if os.path.exists(md_path):
        os.remove(md_path)

    return jsonify({'success': True})


@entries_bp.route('/entries/auto-format', methods=['POST'])
def auto_format_entry():
    """自动格式化行程文本"""
    data = request.get_json()
    if not data or 'raw_text' not in data:
        return jsonify({'error': '缺少 raw_text 字段'}), 400

    raw_text = data['raw_text']
    formatted = auto_format(raw_text)

    return jsonify({
        'raw_text': raw_text,
        'formatted_md': formatted,
    })
