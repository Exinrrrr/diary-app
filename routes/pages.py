"""前端页面路由"""

from flask import Blueprint, render_template

pages_bp = Blueprint('pages', __name__)

@pages_bp.route('/')
def index():
    """主页面 — SPA 入口"""
    return render_template('index.html')
