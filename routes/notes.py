"""工作笔记 API"""

from flask import Blueprint, request, jsonify
from database.db import get_db

notes_bp = Blueprint('notes', __name__)


# ===== 项目 =====

@notes_bp.route('/projects', methods=['GET'])
def list_projects():
    db = get_db()
    rows = db.execute(
        "SELECT p.*, COUNT(n.id) as note_count FROM projects p LEFT JOIN notes n ON n.project_id=p.id GROUP BY p.id ORDER BY p.updated_at DESC"
    ).fetchall()
    return jsonify([dict(r) for r in rows])


@notes_bp.route('/projects', methods=['POST'])
def create_project():
    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({'error': '缺少项目名称'}), 400
    db = get_db()
    cursor = db.execute(
        "INSERT INTO projects (name, description) VALUES (?, ?)",
        (data['name'].strip(), data.get('description', '').strip())
    )
    db.commit()
    row = db.execute("SELECT * FROM projects WHERE id=?", (cursor.lastrowid,)).fetchone()
    return jsonify(dict(row)), 201


@notes_bp.route('/projects/<int:project_id>', methods=['PUT'])
def update_project(project_id):
    data = request.get_json()
    db = get_db()
    row = db.execute("SELECT * FROM projects WHERE id=?", (project_id,)).fetchone()
    if not row:
        return jsonify({'error': '项目不存在'}), 404
    db.execute(
        "UPDATE projects SET name=?, description=?, updated_at=datetime('now','localtime') WHERE id=?",
        (data.get('name', row['name']), data.get('description', row['description']), project_id)
    )
    db.commit()
    row = db.execute("SELECT * FROM projects WHERE id=?", (project_id,)).fetchone()
    return jsonify(dict(row))


@notes_bp.route('/projects/<int:project_id>', methods=['DELETE'])
def delete_project(project_id):
    db = get_db()
    db.execute("DELETE FROM notes WHERE project_id=?", (project_id,))
    db.execute("DELETE FROM projects WHERE id=?", (project_id,))
    db.commit()
    return jsonify({'success': True})


# ===== 笔记 =====

@notes_bp.route('/projects/<int:project_id>/notes', methods=['GET'])
def list_notes(project_id):
    db = get_db()
    rows = db.execute(
        "SELECT * FROM notes WHERE project_id=? ORDER BY updated_at DESC",
        (project_id,)
    ).fetchall()
    return jsonify([dict(r) for r in rows])


@notes_bp.route('/projects/<int:project_id>/notes', methods=['POST'])
def create_note(project_id):
    data = request.get_json()
    if not data:
        return jsonify({'error': '缺少请求体'}), 400
    db = get_db()
    cursor = db.execute(
        "INSERT INTO notes (project_id, title, content_md) VALUES (?, ?, ?)",
        (project_id, data.get('title', '').strip(), data.get('content_md', ''))
    )
    db.commit()
    # 更新项目时间
    db.execute("UPDATE projects SET updated_at=datetime('now','localtime') WHERE id=?", (project_id,))
    db.commit()
    row = db.execute("SELECT * FROM notes WHERE id=?", (cursor.lastrowid,)).fetchone()
    return jsonify(dict(row)), 201


@notes_bp.route('/notes/<int:note_id>', methods=['GET'])
def get_note(note_id):
    db = get_db()
    row = db.execute("SELECT * FROM notes WHERE id=?", (note_id,)).fetchone()
    if not row:
        return jsonify({'error': '笔记不存在'}), 404
    return jsonify(dict(row))


@notes_bp.route('/notes/<int:note_id>', methods=['PUT'])
def update_note(note_id):
    data = request.get_json()
    db = get_db()
    row = db.execute("SELECT * FROM notes WHERE id=?", (note_id,)).fetchone()
    if not row:
        return jsonify({'error': '笔记不存在'}), 404
    db.execute(
        "UPDATE notes SET title=?, content_md=?, updated_at=datetime('now','localtime') WHERE id=?",
        (data.get('title', row['title']), data.get('content_md', row['content_md']), note_id)
    )
    # 更新项目时间
    db.execute("UPDATE projects SET updated_at=datetime('now','localtime') WHERE id=?", (row['project_id'],))
    db.commit()
    row = db.execute("SELECT * FROM notes WHERE id=?", (note_id,)).fetchone()
    return jsonify(dict(row))


@notes_bp.route('/notes/<int:note_id>', methods=['DELETE'])
def delete_note(note_id):
    db = get_db()
    db.execute("DELETE FROM notes WHERE id=?", (note_id,))
    db.commit()
    return jsonify({'success': True})
