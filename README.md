# 📔 实习日记

个人日记 Web 应用，记录日程、照片、提醒和工作笔记。

## 如何启动

### macOS / Windows / Linux

1. 确保安装了 **Python 3.9+**
   - macOS 用户：如果 `python3 --version` 报错，在终端运行 `xcode-select --install`
2. 双击 `启动.command`（macOS）或运行：
```bash
python3 -m venv venv
source venv/bin/activate    # Windows: venv\Scripts\activate
pip install flask Pillow markdown
python3 app.py
```
3. 浏览器打开 http://localhost:5000

## 功能

- 📅 **日历日记** — 点日期写日记，支持 Markdown
- 📷 **照片** — 拖拽上传，自动缩略图
- ✨ **自动排版** — 粘贴行程，自动按时间段分组+emoji
- ⏰ **提醒** — 设置提醒，桌面弹通知
- 📋 **工作笔记** — 按项目分类记录
- 📥 **导入导出** — .zip 完整备份 / .md 纯文档

## 技术栈

Python Flask + SQLite + 原生 HTML/CSS/JS
