"""应用配置"""

import os

# 项目根目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 数据目录
DATA_DIR = os.path.join(BASE_DIR, 'data')
ENTRIES_DIR = os.path.join(DATA_DIR, 'entries')
PHOTOS_DIR = os.path.join(DATA_DIR, 'photos')

# 数据库路径
DATABASE = os.path.join(DATA_DIR, 'diary.db')

# 图片限制
MAX_PHOTO_SIZE = 20 * 1024 * 1024  # 20MB
THUMBNAIL_WIDTH = 300  # 缩略图宽度
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp'}

# Flask 配置
SECRET_KEY = 'diary-app-secret-key-dev'
DEBUG = True
