"""提醒 API 路由"""

from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from database.db import get_db

reminders_bp = Blueprint('reminders', __name__)


def next_remind_at(remind_at: str, rule: str) -> str:
    """根据重复规则计算下一次提醒时间"""
    dt = datetime.fromisoformat(remind_at)
    if rule == 'daily':
        dt += timedelta(days=1)
    elif rule == 'weekly':
        dt += timedelta(weeks=1)
    elif rule == 'monthly':
        # 简单加30天
        dt += timedelta(days=30)
    return dt.isoformat()


@reminders_bp.route('/reminders', methods=['GET'])
def list_reminders():
    """获取提醒列表"""
    status = request.args.get('status', '')
    db = get_db()

    if status == 'active':
        rows = db.execute(
            """SELECT * FROM reminders
               WHERE is_completed = 0
               ORDER BY remind_at ASC"""
        ).fetchall()
    elif status == 'completed':
        rows = db.execute(
            """SELECT * FROM reminders
               WHERE is_completed = 1
               ORDER BY remind_at DESC"""
        ).fetchall()
    else:
        rows = db.execute(
            "SELECT * FROM reminders ORDER BY remind_at ASC"
        ).fetchall()

    return jsonify([dict(r) for r in rows])


@reminders_bp.route('/reminders/due', methods=['GET'])
def get_due_reminders():
    """获取已到期且未处理/未忽略的提醒"""
    now = datetime.now().isoformat()
    db = get_db()
    rows = db.execute(
        """SELECT * FROM reminders
           WHERE remind_at <= ?
             AND is_completed = 0
             AND is_dismissed = 0
           ORDER BY remind_at ASC""",
        (now,)
    ).fetchall()

    return jsonify([dict(r) for r in rows])


@reminders_bp.route('/reminders', methods=['POST'])
def create_reminder():
    """创建提醒"""
    data = request.get_json()
    if not data or 'title' not in data or 'remind_at' not in data:
        return jsonify({'error': '缺少 title 或 remind_at 字段'}), 400

    title = data['title']
    description = data.get('description', '')
    remind_at = data['remind_at']
    entry_date = data.get('entry_date', '')
    is_recurring = data.get('is_recurring', False)
    recurring_rule = data.get('recurring_rule', '')

    db = get_db()
    cursor = db.execute(
        """INSERT INTO reminders (title, description, remind_at, entry_date,
           is_recurring, recurring_rule)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (title, description, remind_at, entry_date,
         1 if is_recurring else 0, recurring_rule)
    )
    db.commit()

    row = db.execute("SELECT * FROM reminders WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return jsonify(dict(row)), 201


@reminders_bp.route('/reminders/<int:reminder_id>', methods=['PUT'])
def update_reminder(reminder_id):
    """更新提醒"""
    data = request.get_json()
    if not data:
        return jsonify({'error': '缺少请求体'}), 400

    db = get_db()
    row = db.execute(
        "SELECT * FROM reminders WHERE id = ?", (reminder_id,)
    ).fetchone()

    if not row:
        return jsonify({'error': '提醒不存在'}), 404

    title = data.get('title', row['title'])
    description = data.get('description', row['description'])
    remind_at = data.get('remind_at', row['remind_at'])
    entry_date = data.get('entry_date', row['entry_date'])
    is_recurring = data.get('is_recurring', row['is_recurring'])
    recurring_rule = data.get('recurring_rule', row['recurring_rule'])
    is_completed = data.get('is_completed', row['is_completed'])
    is_dismissed = data.get('is_dismissed', row['is_dismissed'])

    # 如果标记为完成且是重复提醒，自动生成下一次
    if is_completed and not row['is_completed'] and recurring_rule:
        next_time = next_remind_at(remind_at, recurring_rule)
        db.execute(
            """INSERT INTO reminders (title, description, remind_at, entry_date,
               is_recurring, recurring_rule)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (title, description, next_time, entry_date, 1, recurring_rule)
        )

    db.execute(
        """UPDATE reminders
           SET title=?, description=?, remind_at=?, entry_date=?,
               is_recurring=?, recurring_rule=?, is_completed=?, is_dismissed=?
           WHERE id=?""",
        (title, description, remind_at, entry_date,
         is_recurring, recurring_rule, is_completed, is_dismissed,
         reminder_id)
    )
    db.commit()

    row = db.execute(
        "SELECT * FROM reminders WHERE id = ?", (reminder_id,)
    ).fetchone()
    return jsonify(dict(row))


@reminders_bp.route('/reminders/<int:reminder_id>', methods=['DELETE'])
def delete_reminder(reminder_id):
    """删除提醒"""
    db = get_db()
    db.execute("DELETE FROM reminders WHERE id = ?", (reminder_id,))
    db.commit()
    return jsonify({'success': True})


@reminders_bp.route('/reminders/<int:reminder_id>/dismiss', methods=['POST'])
def dismiss_reminder(reminder_id):
    """忽略提醒（不去除，只是不再弹通知）"""
    db = get_db()
    db.execute(
        "UPDATE reminders SET is_dismissed = 1 WHERE id = ?",
        (reminder_id,)
    )
    db.commit()
    return jsonify({'success': True})
