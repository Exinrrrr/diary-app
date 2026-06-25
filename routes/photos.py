"""照片 API 路由"""

import os
import uuid
from flask import Blueprint, request, jsonify, send_from_directory
from database.db import get_db
from config import PHOTOS_DIR, MAX_PHOTO_SIZE, THUMBNAIL_WIDTH, ALLOWED_EXTENSIONS

photos_bp = Blueprint('photos', __name__)


def allowed_file(filename: str) -> bool:
    """检查文件扩展名是否允许"""
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS


def create_thumbnail(src_path: str, dst_path: str):
    """使用 Pillow 生成缩略图"""
    try:
        from PIL import Image
        img = Image.open(src_path)
        # 转 RGB（处理 PNG 透明通道）
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
        ratio = THUMBNAIL_WIDTH / img.width
        height = int(img.height * ratio)
        img = img.resize((THUMBNAIL_WIDTH, height), Image.LANCZOS)
        img.save(dst_path, 'JPEG', quality=80)
        return True
    except Exception as e:
        print(f'缩略图生成失败: {e}')
        return False


def ensure_entry_exists(date_str: str):
    """确保某天有日记记录（没有则创建空记录）"""
    db = get_db()
    row = db.execute("SELECT id FROM entries WHERE date = ?", (date_str,)).fetchone()
    if not row:
        from config import ENTRIES_DIR
        md_path = os.path.join(ENTRIES_DIR, f'{date_str}.md')
        os.makedirs(os.path.dirname(md_path), exist_ok=True)
        if not os.path.exists(md_path):
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write('')
        cursor = db.execute(
            "INSERT INTO entries (date, title) VALUES (?, '')",
            (date_str,)
        )
        db.commit()
        return cursor.lastrowid
    return row['id']


@photos_bp.route('/photos/upload/<date>', methods=['POST'])
def upload_photos(date):
    """上传照片"""
    if 'photos' not in request.files:
        return jsonify({'error': '没有上传文件'}), 400

    files = request.files.getlist('photos')
    if not files or all(f.filename == '' for f in files):
        return jsonify({'error': '没有选择文件'}), 400

    db = get_db()
    entry_id = ensure_entry_exists(date)

    # 照片目录
    photo_dir = os.path.join(PHOTOS_DIR, date)
    os.makedirs(photo_dir, exist_ok=True)

    results = []

    for file in files:
        if file.filename == '':
            continue

        # 验证
        if not allowed_file(file.filename):
            return jsonify({'error': f'不支持的文件类型: {file.filename}'}), 400

        # 检查大小
        file.seek(0, 2)
        size = file.tell()
        file.seek(0)
        if size > MAX_PHOTO_SIZE:
            return jsonify({'error': f'文件过大: {file.filename}'}), 400

        # 生成文件名
        ext = file.filename.rsplit('.', 1)[1].lower()
        uid = uuid.uuid4().hex[:12]
        filename = f'{uid}.{ext}'
        thumb_filename = f'thumb_{uid}.jpg'

        # 保存原图
        filepath = os.path.join(photo_dir, filename)
        file.save(filepath)

        # 生成缩略图
        thumb_path = os.path.join(photo_dir, thumb_filename)
        create_thumbnail(filepath, thumb_path)

        # 插入数据库
        db.execute(
            """INSERT INTO photos (entry_id, filename, thumb_filename, original_name)
               VALUES (?, ?, ?, ?)""",
            (entry_id, filename, thumb_filename, file.filename)
        )

        results.append({
            'filename': filename,
            'thumb_filename': thumb_filename,
            'original_name': file.filename,
        })

    # 更新 has_photos
    photo_count = db.execute(
        "SELECT COUNT(*) FROM photos WHERE entry_id = ?", (entry_id,)
    ).fetchone()[0]
    db.execute(
        "UPDATE entries SET has_photos = ? WHERE id = ?",
        (1 if photo_count > 0 else 0, entry_id)
    )
    db.commit()

    return jsonify(results), 201


@photos_bp.route('/photos/<int:photo_id>', methods=['DELETE'])
def delete_photo(photo_id):
    """删除照片"""
    db = get_db()
    row = db.execute("SELECT * FROM photos WHERE id = ?", (photo_id,)).fetchone()

    if not row:
        return jsonify({'error': '照片不存在'}), 404

    photo = dict(row)

    # 获取关联日记日期
    entry = db.execute("SELECT date FROM entries WHERE id = ?", (photo['entry_id'],)).fetchone()
    if entry:
        photo_dir = os.path.join(PHOTOS_DIR, entry['date'])
        for fname in [photo['filename'], photo['thumb_filename']]:
            filepath = os.path.join(photo_dir, fname)
            if os.path.exists(filepath):
                os.remove(filepath)

    db.execute("DELETE FROM photos WHERE id = ?", (photo_id,))

    # 更新 has_photos
    photo_count = db.execute(
        "SELECT COUNT(*) FROM photos WHERE entry_id = ?", (photo['entry_id'],)
    ).fetchone()[0]
    db.execute(
        "UPDATE entries SET has_photos = ? WHERE id = ?",
        (1 if photo_count > 0 else 0, photo['entry_id'])
    )

    db.commit()
    return jsonify({'success': True})


@photos_bp.route('/photos/<date>/<filename>')
def serve_photo(date, filename):
    """提供照片文件"""
    photo_dir = os.path.join(PHOTOS_DIR, date)
    return send_from_directory(photo_dir, filename)
