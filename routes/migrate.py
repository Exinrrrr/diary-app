"""迁移 API 路由"""

import os
from flask import Blueprint, request, jsonify
from services.migration import migrate_existing_diary

migrate_bp = Blueprint('migrate', __name__)


@migrate_bp.route('/migrate', methods=['POST'])
def migrate():
    """导入旧的 北京实习日记.md"""
    # 旧日记路径（相对于 diary-app 的上级目录）
    source_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        '..',
        '北京实习日记.md'
    )
    source_path = os.path.normpath(source_path)

    # 也尝试在 AI 目录下查找
    if not os.path.exists(source_path):
        source_path = '/Users/exinrr/Documents/AI/北京实习日记.md'

    if not os.path.exists(source_path):
        return jsonify({'error': f'找不到旧日记文件: {source_path}'}), 404

    result = migrate_existing_diary(source_path)
    return jsonify(result)
