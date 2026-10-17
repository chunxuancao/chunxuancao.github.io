#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一键启动文章管理后台"""
import subprocess
import sys
import webbrowser
import time
from pathlib import Path

ADMIN_DIR = Path(__file__).parent
MAIN_PY = ADMIN_DIR / "main.py"

print("🐱 喵喵小码 - 文章管理后台")
print("=" * 40)
print()

# 检查依赖
try:
    import fastapi
    import uvicorn
except ImportError:
    print("📦 正在安装依赖...")
    subprocess.run([sys.executable, "-m", "pip", "install", "fastapi", "uvicorn"], cwd=str(ADMIN_DIR))
    print()

print("🚀 启动服务中...")
print("📝 管理后台: http://localhost:5000")
print("💡 按 Ctrl+C 停止服务")
print()

# 延迟打开浏览器
def open_browser():
    time.sleep(3)
    webbrowser.open("http://localhost:5000")

import threading
threading.Thread(target=open_browser, daemon=True).start()

# 启动服务
subprocess.run([sys.executable, str(MAIN_PY)], cwd=str(ADMIN_DIR.parent))
