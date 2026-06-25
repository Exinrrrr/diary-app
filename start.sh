#!/bin/bash
# 实习日记应用启动脚本
cd "$(dirname "$0")"
source venv/bin/activate
echo "正在启动实习日记..."
python3 app.py
