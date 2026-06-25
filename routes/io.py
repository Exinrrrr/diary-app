"""导入导出 API"""

import os
import io as io_module
import zipfile
import json
import shutil
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file, current_app
from database.db import get_db
from config import ENTRIES_DIR, PHOTOS_DIR, DATA_DIR

io_bp = Blueprint('io', __name__)


def rebuild_photo_records(db):
    """从磁盘照片文件重建 photos 表记录"""
    # 先清空不存在的记录
    for date_dir in os.listdir(PHOTOS_DIR) if os.path.isdir(PHOTOS_DIR) else []:
        date_path = os.path.join(PHOTOS_DIR, date_dir)
        if not os.path.isdir(date_path):
            continue
        entry = db.execute("SELECT id FROM entries WHERE date=?", (date_dir,)).fetchone()
        if not entry:
            continue
        entry_id = entry['id']
        for fname in sorted(os.listdir(date_path)):
            if fname.startswith('thumb_') or fname.startswith('.'):
                continue
            fpath = os.path.join(date_path, fname)
            if not os.path.isfile(fpath):
                continue
            # 找对应缩略图
            name_no_ext = os.path.splitext(fname)[0]
            thumb = fname
            for t in sorted(os.listdir(date_path)):
                if t.startswith(f'thumb_{name_no_ext}'):
                    thumb = t
                    break
            # 检查是否已存在
            existing = db.execute(
                "SELECT id FROM photos WHERE entry_id=? AND filename=?",
                (entry_id, fname)
            ).fetchone()
            if existing:
                continue
            db.execute(
                "INSERT INTO photos (entry_id, filename, thumb_filename, original_name) VALUES (?,?,?,?)",
                (entry_id, fname, thumb, fname)
            )
        # 更新 has_photos 标记
        count = db.execute("SELECT COUNT(*) FROM photos WHERE entry_id=?", (entry_id,)).fetchone()[0]
        db.execute("UPDATE entries SET has_photos=? WHERE id=?", (1 if count > 0 else 0, entry_id))


def collect_metadata():
    """收集所有元数据（entries + reminders），用于导出"""
    db = get_db()
    entries = db.execute("SELECT * FROM entries ORDER BY date").fetchall()
    reminders = db.execute("SELECT * FROM reminders ORDER BY remind_at").fetchall()
    projects = db.execute("SELECT * FROM projects ORDER BY id").fetchall()
    notes = db.execute("SELECT * FROM notes ORDER BY id").fetchall()
    return {
        'version': 2,
        'exported_at': datetime.now().isoformat(),
        'entries': [dict(e) for e in entries],
        'reminders': [dict(r) for r in reminders],
        'projects': [dict(p) for p in projects],
        'notes': [dict(n) for n in notes],
    }


@io_bp.route('/export/backup', methods=['GET'])
def export_backup():
    """导出完整备份 ZIP（日记 + 照片 + 元数据）"""
    metadata = collect_metadata()
    buf = io_module.BytesIO()

    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        # 元数据 JSON
        zf.writestr('metadata.json', json.dumps(metadata, ensure_ascii=False, indent=2))

        # 所有日记 .md 文件
        if os.path.isdir(ENTRIES_DIR):
            for fname in os.listdir(ENTRIES_DIR):
                if fname.endswith('.md'):
                    fpath = os.path.join(ENTRIES_DIR, fname)
                    zf.write(fpath, f'entries/{fname}')

        # 所有照片
        if os.path.isdir(PHOTOS_DIR):
            for date_dir in os.listdir(PHOTOS_DIR):
                date_path = os.path.join(PHOTOS_DIR, date_dir)
                if os.path.isdir(date_path):
                    for fname in os.listdir(date_path):
                        fpath = os.path.join(date_path, fname)
                        zf.write(fpath, f'photos/{date_dir}/{fname}')

    buf.seek(0)
    date_str = datetime.now().strftime('%Y-%m-%d')
    return send_file(
        buf,
        mimetype='application/zip',
        as_attachment=True,
        download_name=f'diary_backup_{date_str}.zip',
    )


@io_bp.route('/export/markdown', methods=['GET'])
def export_markdown():
    """导出纯 Markdown 文档（适合交给大模型分析）"""
    db = get_db()
    entries = db.execute("SELECT * FROM entries ORDER BY date").fetchall()
    reminders = db.execute("SELECT * FROM reminders ORDER BY remind_at").fetchall()
    projects = db.execute("SELECT * FROM projects ORDER BY id").fetchall()
    notes = db.execute("SELECT n.*, p.name as project_name FROM notes n LEFT JOIN projects p ON p.id=n.project_id ORDER BY n.project_id, n.updated_at DESC").fetchall()

    lines = []
    lines.append('# 北京实习日记')
    lines.append(f'> 导出时间：{datetime.now().strftime("%Y年%m月%d日 %H:%M")}')
    lines.append(f'> 共 {len(entries)} 天日记，{len(reminders)} 条提醒，{len(projects)} 个项目，{len(notes)} 条笔记')
    lines.append('')
    lines.append('---')
    lines.append('')

    for i, entry in enumerate(entries):
        date = entry['date']
        title = entry['title'] or '无标题'
        # 解析日期为中文
        try:
            d = datetime.strptime(date, '%Y-%m-%d')
            weekdays = ['一', '二', '三', '四', '五', '六', '日']
            cn_date = f'{d.year}年{d.month}月{d.day}日 · 星期{weekdays[d.weekday()]}'
            day_label = f'第{i + 1}天（{d.month}月{d.day}日）'
        except:
            cn_date = date
            day_label = f'第{i + 1}天'

        lines.append(f'## {day_label} —— {title}')
        lines.append('')

        # 读取 markdown 内容
        md_path = os.path.join(ENTRIES_DIR, f'{date}.md')
        if os.path.exists(md_path):
            with open(md_path, 'r', encoding='utf-8') as f:
                content = f.read()
            lines.append(content)
        else:
            lines.append('（无内容）')

        lines.append('')
        lines.append('---')
        lines.append('')

    # 提醒列表
    if reminders:
        lines.append('## 📋 提醒列表')
        lines.append('')
        for r in reminders:
            try:
                rt = datetime.fromisoformat(r['remind_at'])
                time_str = rt.strftime('%m月%d日 %H:%M')
            except:
                time_str = r['remind_at']
            status = '✅' if r['is_completed'] else '⏰'
            recurring = {'daily': ' · 每天', 'weekly': ' · 每周', 'monthly': ' · 每月'}.get(r['recurring_rule'], '')
            lines.append(f'- {status} **{r["title"]}** — {time_str}{recurring}')
            if r['description']:
                lines.append(f'  > {r["description"]}')
        lines.append('')

    # 工作笔记
    if projects:
        lines.append('## 📋 工作笔记')
        lines.append('')
        for proj in projects:
            lines.append(f'### {proj["name"]}')
            if proj['description']:
                lines.append(f'> {proj["description"]}')
            lines.append('')
            proj_notes = [n for n in notes if n['project_id'] == proj['id']]
            for note in proj_notes:
                lines.append(f'#### {note["title"] or "无标题"}')
                lines.append('')
                if note['content_md']:
                    lines.append(note['content_md'])
                lines.append('')
        lines.append('')

    result = '\n'.join(lines)
    buf = io_module.BytesIO(result.encode('utf-8'))
    date_str = datetime.now().strftime('%Y-%m-%d')
    return send_file(
        buf,
        mimetype='text/markdown; charset=utf-8',
        as_attachment=True,
        download_name=f'diary_export_{date_str}.md',
    )


@io_bp.route('/import', methods=['POST'])
def import_backup():
    """导入备份 ZIP"""
    mode = request.args.get('mode', 'merge')  # 'overwrite' or 'merge'

    if 'file' not in request.files:
        return jsonify({'error': '没有上传文件'}), 400

    file = request.files['file']
    if not file.filename or not file.filename.endswith('.zip'):
        return jsonify({'error': '只支持 .zip 文件'}), 400

    db = get_db()

    # 如果是覆盖模式，先清空
    if mode == 'overwrite':
        # 清空数据库
        db.execute("DELETE FROM photos")
        db.execute("DELETE FROM notes")
        db.execute("DELETE FROM projects")
        db.execute("DELETE FROM reminders")
        db.execute("DELETE FROM entries")
        db.commit()

        # 清空文件
        for d in [ENTRIES_DIR, PHOTOS_DIR]:
            if os.path.isdir(d):
                shutil.rmtree(d)
            os.makedirs(d, exist_ok=True)

    # 解压并导入
    merged_count = 0
    created_count = 0
    skipped_count = 0
    errors = []

    try:
        # 先将上传文件读入内存，避免 Flask FileStorage 的流兼容问题
        file_data = file.read()
        log_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'import_debug.log')
        with open(log_path, 'a') as logf:
            logf.write(f"[IMPORT] file={file.filename}, size={len(file_data)}, mode={mode}\n")
        zip_data = io_module.BytesIO(file_data)
        with zipfile.ZipFile(zip_data) as zf:
            namelist = zf.namelist()
            with open(log_path, 'a') as logf:
                logf.write(f"[IMPORT] zip has {len(namelist)} files, metadata={'metadata.json' in namelist}\n")
            # 先处理 metadata.json
            if 'metadata.json' in zf.namelist():
                metadata = json.loads(zf.read('metadata.json').decode('utf-8'))
                with open(log_path, 'a') as logf:
                    logf.write(f"[IMPORT] metadata: {len(metadata.get('entries',[]))} entries\n")

                for entry_data in metadata.get('entries', []):
                    date = entry_data['date']
                    existing = db.execute(
                        "SELECT id, updated_at FROM entries WHERE date = ?", (date,)
                    ).fetchone()

                    if existing:
                        if mode == 'merge':
                            import_updated = entry_data.get('updated_at', '')
                            local_updated = existing['updated_at']
                            if import_updated <= local_updated:
                                skipped_count += 1
                                continue
                        db.execute(
                            """UPDATE entries SET title=?, word_count=?, has_photos=?,
                               mood=?, updated_at=? WHERE date=?""",
                            (entry_data.get('title', ''), entry_data.get('word_count', 0),
                             entry_data.get('has_photos', 0), entry_data.get('mood', ''),
                             entry_data.get('updated_at', ''), date)
                        )
                        merged_count += 1
                    else:
                        db.execute(
                            """INSERT INTO entries (date, title, word_count, has_photos, mood, created_at, updated_at)
                               VALUES (?, ?, ?, ?, ?, ?, ?)""",
                            (date, entry_data.get('title', ''),
                             entry_data.get('word_count', 0),
                             entry_data.get('has_photos', 0),
                             entry_data.get('mood', ''),
                             entry_data.get('created_at', ''),
                             entry_data.get('updated_at', ''))
                        )
                        created_count += 1

                for rem_data in metadata.get('reminders', []):
                    if mode == 'merge':
                        existing_rem = db.execute(
                            "SELECT id FROM reminders WHERE id = ?", (rem_data['id'],)
                        ).fetchone()
                        if existing_rem:
                            skipped_count += 1
                            continue
                    db.execute(
                        """INSERT INTO reminders (id, title, description, remind_at, entry_date,
                           is_recurring, recurring_rule, is_completed, is_dismissed, created_at)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (rem_data['id'], rem_data['title'], rem_data.get('description', ''),
                         rem_data['remind_at'], rem_data.get('entry_date', ''),
                         rem_data.get('is_recurring', 0), rem_data.get('recurring_rule', ''),
                         rem_data.get('is_completed', 0), rem_data.get('is_dismissed', 0),
                         rem_data.get('created_at', ''))
                    )

                # 导入项目
                project_id_map = {}  # old_id → new_id
                for proj_data in metadata.get('projects', []):
                    if mode == 'merge':
                        existing = db.execute(
                            "SELECT id FROM projects WHERE name=?", (proj_data['name'],)
                        ).fetchone()
                        if existing:
                            project_id_map[proj_data['id']] = existing['id']
                            continue
                    cursor = db.execute(
                        "INSERT INTO projects (name, description) VALUES (?,?)",
                        (proj_data['name'], proj_data.get('description', ''))
                    )
                    project_id_map[proj_data['id']] = cursor.lastrowid

                # 导入笔记
                for note_data in metadata.get('notes', []):
                    old_pid = note_data['project_id']
                    new_pid = project_id_map.get(old_pid)
                    if new_pid is None:
                        continue
                    if mode == 'merge':
                        existing = db.execute(
                            "SELECT id FROM notes WHERE project_id=? AND title=?",
                            (new_pid, note_data['title'])
                        ).fetchone()
                        if existing:
                            continue
                    db.execute(
                        """INSERT INTO notes (project_id, title, content_md)
                           VALUES (?,?,?)""",
                        (new_pid, note_data.get('title', ''), note_data.get('content_md', ''))
                    )
            else:
                # 无 metadata.json 时，从 entries/*.md 文件重建
                with open(log_path, 'a') as logf:
                    logf.write("[IMPORT] no metadata.json, reconstructing from files\n")
                for name in namelist:
                    if name.startswith('entries/') and name.endswith('.md'):
                        fname = name.replace('entries/', '')
                        date = fname.replace('.md', '')
                        # 读文件内容获取字数
                        content = zf.read(name).decode('utf-8', errors='replace')
                        word_count = len(content)
                        # 检查是否已存在
                        existing = db.execute(
                            "SELECT id FROM entries WHERE date = ?", (date,)
                        ).fetchone()
                        if existing:
                            if mode == 'merge':
                                skipped_count += 1
                                continue
                            db.execute(
                                "UPDATE entries SET word_count=?, updated_at=datetime('now','localtime') WHERE date=?",
                                (word_count, date)
                            )
                            merged_count += 1
                        else:
                            db.execute(
                                "INSERT INTO entries (date, word_count) VALUES (?, ?)",
                                (date, word_count)
                            )
                            created_count += 1

            # 解压 entries/ 目录
            for name in zf.namelist():
                if name.startswith('entries/') and name.endswith('.md'):
                    fname = os.path.basename(name)
                    dest = os.path.join(ENTRIES_DIR, fname)
                    # 合并模式下，如果文件已存在且不是覆盖的条目则跳过
                    if mode == 'merge' and os.path.exists(dest):
                        # 文件内容由上面 metadata 处理决定是否覆盖
                        date_str = fname.replace('.md', '')
                        # 检查是否在上面被 skipped 了
                        pass
                    os.makedirs(os.path.dirname(dest), exist_ok=True)
                    with open(dest, 'wb') as f:
                        f.write(zf.read(name))

                # 解压 photos/
                elif name.startswith('photos/') and not name.endswith('/'):
                    # 路径格式: photos/2026-06-17/xxx.jpg
                    rel_path = name[7:]  # 去掉 'photos/'
                    dest = os.path.join(PHOTOS_DIR, rel_path)
                    os.makedirs(os.path.dirname(dest), exist_ok=True)
                    with open(dest, 'wb') as f:
                        f.write(zf.read(name))

        # 从磁盘照片文件重建 photos 表
        rebuild_photo_records(db)

        db.commit()

    except Exception as e:
        db.rollback()
        return jsonify({'error': f'导入失败：{str(e)}'}), 500

    return jsonify({
        'success': True,
        'mode': mode,
        'merged': merged_count,
        'created': created_count,
        'skipped': skipped_count,
        'errors': errors,
    })


@io_bp.route('/import/markdown', methods=['POST'])
def import_markdown():
    """从 .md 文件导入日记（使用 migration 解析器，兼容北京实习日记.md 格式）"""
    mode = request.args.get('mode', 'merge')

    if 'file' not in request.files:
        return jsonify({'error': '没有上传文件'}), 400

    file = request.files['file']
    if not file.filename:
        return jsonify({'error': '无效文件'}), 400

    # 读文件内容并解析
    from services.migration import parse_existing_diary as parse_md
    import tempfile

    tmp_path = os.path.join(DATA_DIR, '_temp_import.md')
    file.save(tmp_path)

    try:
        entries_data = parse_md(tmp_path)
    except Exception as e:
        os.remove(tmp_path)
        return jsonify({'error': f'解析 .md 文件失败：{str(e)}'}), 400
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    if not entries_data:
        return jsonify({'error': '文件中没有找到日记条目'}), 400

    db = get_db()

    if mode == 'overwrite':
        from config import PHOTOS_DIR
        db.execute("DELETE FROM photos")
        db.execute("DELETE FROM reminders")
        db.execute("DELETE FROM entries")
        db.commit()
        for d in [ENTRIES_DIR]:
            if os.path.isdir(d):
                shutil.rmtree(d)
            os.makedirs(d, exist_ok=True)

    merged_count = 0
    created_count = 0
    skipped_count = 0

    for entry in entries_data:
        date = entry['date']
        title = entry.get('title', '')
        content_md = entry.get('content_md', '')

        existing = db.execute("SELECT id FROM entries WHERE date=?", (date,)).fetchone()
        if existing:
            if mode == 'merge':
                skipped_count += 1
                continue
            db.execute(
                "UPDATE entries SET title=?, updated_at=datetime('now','localtime') WHERE date=?",
                (title, date)
            )
            merged_count += 1
        else:
            db.execute(
                "INSERT INTO entries (date, title, word_count) VALUES (?,?,?)",
                (date, title, len(content_md))
            )
            created_count += 1

        # 写入 markdown 文件
        md_path = os.path.join(ENTRIES_DIR, f'{date}.md')
        full = f'# {title}\n\n{content_md}' if title else content_md
        os.makedirs(os.path.dirname(md_path), exist_ok=True)
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(full)

    db.commit()

    return jsonify({
        'success': True,
        'mode': mode,
        'merged': merged_count,
        'created': created_count,
        'skipped': skipped_count,
    })
