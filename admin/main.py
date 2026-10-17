#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
喵喵小码 - 文章管理后台
FastAPI + 静态前端
"""
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pathlib import Path
import re
import base64
import threading
import sys
import os
import uuid
import shutil
import time
from datetime import datetime

# 导入GitHub配置（不推送到GitHub）
sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))
try:
    from local_config import GITHUB_TOKEN as TOKEN, GITHUB_OWNER as OWNER, GITHUB_REPO as REPO, GITHUB_BRANCH as BRANCH
    GITHUB_AVAILABLE = True
except ImportError:
    TOKEN = OWNER = REPO = BRANCH = ""
    GITHUB_AVAILABLE = False

import requests

app = FastAPI(title="喵喵小码 - 文章管理后台")

BLOG_ROOT = Path(__file__).parent.parent
POSTS_DIR = BLOG_ROOT / "source" / "_posts"
ADMIN_DIR = Path(__file__).parent

GITHUB_API = "https://api.github.com"
GITHUB_HEADERS = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

# 不推送的文件
EXCLUDE_FILES = {
    "tools/local_config.py",
    "tools/debug_push.py",
}

# ========== 部署状态 ==========
_deploy_state = {
    "running": False,
    "cancelled": False,
    "progress": 0,
    "stage": "",
    "logs": [],
    "result": None,  # "success" / "failed" / "cancelled" / None
    "error": "",
    "start_time": None,
}
_deploy_lock = threading.Lock()


def _deploy_log(msg):
    """添加部署日志"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    _deploy_state["logs"].append(f"[{timestamp}] {msg}")
    # 只保留最后100条
    if len(_deploy_state["logs"]) > 100:
        _deploy_state["logs"] = _deploy_state["logs"][-100:]
    print(f"🚀 {msg}")


def _deploy_set_progress(progress, stage):
    """设置部署进度"""
    _deploy_state["progress"] = min(100, max(0, progress))
    _deploy_state["stage"] = stage
    _deploy_log(f"📊 {stage} ({progress}%)")


def _deploy_check_cancel():
    """检查是否取消"""
    return _deploy_state["cancelled"]


def _collect_deploy_files():
    """收集要推送的文件"""
    files = []

    def add_file(rel_path, abs_path):
        if rel_path in EXCLUDE_FILES:
            return
        if not abs_path.exists():
            return
        content = abs_path.read_text(encoding="utf-8")
        if not content or len(content.strip()) == 0:
            return
        files.append({"path": rel_path, "content": content})

    # CSS + JS
    add_file("source/css/cat-theme.css", BLOG_ROOT / "source" / "css" / "cat-theme.css")
    add_file("source/js/cat-theme.js", BLOG_ROOT / "source" / "js" / "cat-theme.js")
    # 配置
    add_file("_config.butterfly.yml", BLOG_ROOT / "_config.butterfly.yml")
    # 文章
    for md in sorted(POSTS_DIR.glob("*.md")):
        add_file(f"source/_posts/{md.name}", md)
    # 工具脚本
    tools_dir = BLOG_ROOT / "tools"
    if tools_dir.exists():
        for py in sorted(tools_dir.glob("*.py")):
            add_file(f"tools/{py.name}", py)
    # 管理后台
    admin_dir = BLOG_ROOT / "admin"
    if admin_dir.exists():
        add_file("admin/main.py", admin_dir / "main.py")
        add_file("admin/start.py", admin_dir / "start.py")
        add_file("admin/requirements.txt", admin_dir / "requirements.txt")
        add_file("admin/static/index.html", admin_dir / "static" / "index.html")
    # 一键脚本
    for bat in ["start-blog.bat", "stop-blog.bat", "deploy-blog.bat", "start-admin.bat"]:
        add_file(bat, BLOG_ROOT / bat)

    return files


def _git_blob_hash(content):
    """计算GitHub blob hash（用于对比文件是否修改）"""
    import hashlib
    data = content.encode("utf-8")
    header = f"blob {len(data)}\0".encode("utf-8")
    return hashlib.sha1(header + data).hexdigest()


# 全局配置
AUTO_SYNC_ENABLED = True  # 单文件自动同步开关


def push_single_file(github_path, content, commit_message=""):
    """单文件推送到GitHub（轻量级，不走完整部署流程）
    返回 (success, message)
    """
    # 如果关闭了自动同步，直接返回成功但不推送
    if not AUTO_SYNC_ENABLED:
        return True, "自动同步已关闭，文件仅保存在本地"
    try:
        if not commit_message:
            commit_message = f"🐱 更新: {github_path}"

        # 1. 获取当前分支最新commit
        ref = requests.get(f"{GITHUB_API}/repos/{OWNER}/{REPO}/git/ref/heads/{BRANCH}",
                           headers=GITHUB_HEADERS, timeout=30)
        ref.raise_for_status()
        commit_sha = ref.json()['object']['sha']

        commit = requests.get(f"{GITHUB_API}/repos/{OWNER}/{REPO}/git/commits/{commit_sha}",
                              headers=GITHUB_HEADERS, timeout=30)
        commit.raise_for_status()
        tree_sha = commit.json()['tree']['sha']

        # 2. 创建blob
        content_b64 = base64.b64encode(content.encode("utf-8")).decode("ascii")
        r = requests.post(f"{GITHUB_API}/repos/{OWNER}/{REPO}/git/blobs",
                          headers=GITHUB_HEADERS,
                          json={"content": content_b64, "encoding": "base64"},
                          timeout=30)
        r.raise_for_status()
        blob_sha = r.json()["sha"]

        # 3. 创建新tree（只更新这一个文件）
        r = requests.post(f"{GITHUB_API}/repos/{OWNER}/{REPO}/git/trees",
                          headers=GITHUB_HEADERS,
                          json={"base_tree": tree_sha, "tree": [{
                              "path": github_path,
                              "mode": "100644",
                              "type": "blob",
                              "sha": blob_sha,
                          }]},
                          timeout=30)
        r.raise_for_status()
        new_tree_sha = r.json()["sha"]

        # 4. 创建commit
        r = requests.post(f"{GITHUB_API}/repos/{OWNER}/{REPO}/git/commits",
                          headers=GITHUB_HEADERS,
                          json={
                              "message": commit_message,
                              "tree": new_tree_sha,
                              "parents": [commit_sha],
                          },
                          timeout=30)
        r.raise_for_status()
        new_commit_sha = r.json()["sha"]

        # 5. 更新分支引用
        r = requests.patch(f"{GITHUB_API}/repos/{OWNER}/{REPO}/git/refs/heads/{BRANCH}",
                           headers=GITHUB_HEADERS,
                           json={"sha": new_commit_sha, "force": False},
                           timeout=30)
        r.raise_for_status()

        return True, f"已推送: {github_path}"
    except Exception as e:
        return False, f"推送失败: {str(e)[:200]}"


def _deploy_worker(mode="full"):
    """部署工作线程
    mode: fast=快速部署(只推修改过的文件,不删除) / full=完整同步(全推+删除) / posts_only=仅推文章
    """
    global _deploy_state
    mode_names = {"fast": "快速部署", "full": "完整同步", "posts_only": "仅推送文章"}
    try:
        _deploy_state["running"] = True
        _deploy_state["cancelled"] = False
        _deploy_state["progress"] = 0
        _deploy_state["stage"] = "初始化"
        _deploy_state["logs"] = []
        _deploy_state["result"] = None
        _deploy_state["error"] = ""
        _deploy_state["start_time"] = time.time()

        if not GITHUB_AVAILABLE:
            raise Exception("GitHub配置文件不存在，请检查 tools/local_config.py")

        _deploy_log(f"📦 部署模式: {mode_names.get(mode, mode)}")

        # 阶段1: 获取分支信息 (5%)
        _deploy_set_progress(2, "获取当前分支信息")
        ref = requests.get(f"{GITHUB_API}/repos/{OWNER}/{REPO}/git/ref/heads/{BRANCH}",
                           headers=GITHUB_HEADERS, timeout=30)
        ref.raise_for_status()
        commit_sha = ref.json()["object"]["sha"]
        _deploy_log(f"当前commit: {commit_sha[:8]}")

        if _deploy_check_cancel():
            raise _DeployCancelled()

        commit = requests.get(f"{GITHUB_API}/repos/{OWNER}/{REPO}/git/commits/{commit_sha}",
                              headers=GITHUB_HEADERS, timeout=30)
        commit.raise_for_status()
        tree_sha = commit.json()["tree"]["sha"]
        _deploy_log(f"当前tree: {tree_sha[:8]}")

        # 阶段2: 收集文件 (10%)
        _deploy_set_progress(8, "收集待推送文件")
        files_to_push = _collect_deploy_files()

        # 根据模式过滤文件
        if mode == "posts_only":
            files_to_push = [f for f in files_to_push if f["path"].startswith("source/_posts/")]
            _deploy_log(f"仅推送文章模式，筛选后: {len(files_to_push)} 个文件")
        elif mode == "fast":
            # 快速模式：获取远端文件hash，只推送有修改的
            _deploy_log("快速模式：对比远端文件hash，仅推送修改过的文件...")
            remote_tree = requests.get(f"{GITHUB_API}/repos/{OWNER}/{REPO}/git/trees/{tree_sha}?recursive=1",
                                       headers=GITHUB_HEADERS, timeout=30)
            remote_tree.raise_for_status()
            remote_hashes = {item["path"]: item.get("sha") for item in remote_tree.json().get("tree", []) if item.get("type") == "blob"}

            changed_files = []
            for f in files_to_push:
                local_hash = _git_blob_hash(f["content"])
                remote_hash = remote_hashes.get(f["path"])
                if remote_hash != local_hash:
                    changed_files.append(f)
            files_to_push = changed_files
            _deploy_log(f"快速模式：发现 {len(files_to_push)} 个文件有修改")
        else:
            _deploy_log(f"完整同步模式：待推送 {len(files_to_push)} 个文件")

        if _deploy_check_cancel():
            raise _DeployCancelled()

        # 阶段3: 创建blobs (10%-70%)
        if files_to_push:
            _deploy_set_progress(10, f"创建文件blob (0/{len(files_to_push)})")
            tree_items = []
            for i, f in enumerate(files_to_push, 1):
                if _deploy_check_cancel():
                    raise _DeployCancelled()
                content_b64 = base64.b64encode(f["content"].encode("utf-8")).decode("ascii")
                r = requests.post(f"{GITHUB_API}/repos/{OWNER}/{REPO}/git/blobs",
                                  headers=GITHUB_HEADERS,
                                  json={"content": content_b64, "encoding": "base64"},
                                  timeout=30)
                if r.status_code != 201:
                    raise Exception(f"文件 {f['path']} 创建blob失败: HTTP {r.status_code} - {r.text[:200]}")
                blob_sha = r.json()["sha"]
                tree_items.append({
                    "path": f["path"],
                    "mode": "100644",
                    "type": "blob",
                    "sha": blob_sha,
                })
                # 进度从10%到70%
                progress = 10 + int(60 * i / len(files_to_push))
                if i % 5 == 0 or i == len(files_to_push):
                    _deploy_set_progress(progress, f"创建文件blob ({i}/{len(files_to_push)})")
            _deploy_log(f"全部 {len(tree_items)} 个blob创建完成")
        else:
            tree_items = []
            _deploy_log("没有文件需要推送，跳过blob创建")
            _deploy_set_progress(70, "无文件变更")

        # 阶段3.5: 同步删除远端多余文件 (仅full模式) (72%)
        if mode == "full":
            _deploy_set_progress(72, "检查远端待删除文件")
            if _deploy_check_cancel():
                raise _DeployCancelled()

            # 递归获取远端当前tree中的所有文件
            remote_tree = requests.get(f"{GITHUB_API}/repos/{OWNER}/{REPO}/git/trees/{tree_sha}?recursive=1",
                                       headers=GITHUB_HEADERS, timeout=30)
        remote_tree.raise_for_status()
        remote_files = {item["path"] for item in remote_tree.json().get("tree", []) if item.get("type") == "blob"}

        # 本地要推送的文件路径集合
        local_paths = {f["path"] for f in files_to_push}

        # 我们管理的目录前缀（只删除这些目录下的文件）
        managed_prefixes = (
            "source/_posts/",
            "source/css/",
            "source/js/",
            "admin/",
            "tools/",
        )
        managed_files = ("_config.butterfly.yml", "start-blog.bat", "stop-blog.bat",
                         "deploy-blog.bat", "start-admin.bat")

        # 找出远端存在但本地不存在、且在我们管理范围内的文件
        files_to_delete = []
        for remote_path in remote_files:
            if remote_path in local_paths:
                continue
            # 检查是否在管理范围内
            in_managed = any(remote_path.startswith(prefix) for prefix in managed_prefixes)
            in_managed = in_managed or remote_path in managed_files
            if in_managed:
                files_to_delete.append(remote_path)

        if files_to_delete:
            _deploy_log(f"发现 {len(files_to_delete)} 个远端多余文件，将删除:")
            for f in files_to_delete:
                _deploy_log(f"  🗑️  {f}")
                # GitHub API删除文件：sha设为null
                tree_items.append({
                    "path": f,
                    "mode": "100644",
                    "type": "blob",
                    "sha": None,
                })
        else:
            _deploy_log("远端无多余文件，无需删除")

        # 阶段4: 创建tree (80%)
        _deploy_set_progress(75, "创建新tree")
        if _deploy_check_cancel():
            raise _DeployCancelled()
        r = requests.post(f"{GITHUB_API}/repos/{OWNER}/{REPO}/git/trees",
                          headers=GITHUB_HEADERS,
                          json={"base_tree": tree_sha, "tree": tree_items},
                          timeout=30)
        r.raise_for_status()
        new_tree_sha = r.json()["sha"]
        _deploy_log(f"新tree: {new_tree_sha[:8]}")

        # 阶段5: 创建commit (90%)
        _deploy_set_progress(85, "创建commit")
        if _deploy_check_cancel():
            raise _DeployCancelled()
        r = requests.post(f"{GITHUB_API}/repos/{OWNER}/{REPO}/git/commits",
                          headers=GITHUB_HEADERS,
                          json={
                              "message": "🐱 喵喵小码 - 文章更新",
                              "tree": new_tree_sha,
                              "parents": [commit_sha],
                          },
                          timeout=30)
        r.raise_for_status()
        new_commit_sha = r.json()["sha"]
        _deploy_log(f"新commit: {new_commit_sha[:8]}")

        # 阶段6: 更新分支ref (100%)
        _deploy_set_progress(95, "更新分支ref")
        if _deploy_check_cancel():
            raise _DeployCancelled()
        r = requests.patch(f"{GITHUB_API}/repos/{OWNER}/{REPO}/git/refs/heads/{BRANCH}",
                           headers=GITHUB_HEADERS,
                           json={"sha": new_commit_sha, "force": False},
                           timeout=30)
        r.raise_for_status()

        _deploy_set_progress(100, "部署完成")
        _deploy_log("✅ 推送完成！GitHub Actions 正在构建（约1-2分钟）")
        _deploy_log("🌐 线上博客: https://chunxuancao.github.io/")
        _deploy_state["result"] = "success"

    except _DeployCancelled:
        _deploy_log("⚠️ 部署已取消")
        _deploy_state["result"] = "cancelled"
        _deploy_state["error"] = "用户取消了部署"
    except Exception as e:
        _deploy_log(f"❌ 部署失败: {e}")
        _deploy_state["result"] = "failed"
        _deploy_state["error"] = str(e)
    finally:
        _deploy_state["running"] = False
        _deploy_lock.release()


class _DeployCancelled(Exception):
    """部署取消异常"""
    pass


# ========== 部署API ==========
@app.post("/api/deploy/start")
def deploy_start():
    """启动部署（异步，完整同步：推送全部 + 删除远端多余文件）"""
    if not _deploy_lock.acquire(blocking=False):
        return {"status": "busy", "message": "已有部署任务正在运行"}
    # 启动工作线程，固定用full模式
    thread = threading.Thread(target=_deploy_worker, args=("full",), daemon=True)
    thread.start()
    return {"status": "started", "message": "部署已启动"}


@app.get("/api/deploy/status")
def deploy_status():
    """查询部署状态"""
    elapsed = 0
    if _deploy_state["start_time"]:
        elapsed = int(time.time() - _deploy_state["start_time"])
    return {
        "running": _deploy_state["running"],
        "cancelled": _deploy_state["cancelled"],
        "progress": _deploy_state["progress"],
        "stage": _deploy_state["stage"],
        "logs": _deploy_state["logs"],
        "result": _deploy_state["result"],
        "error": _deploy_state["error"],
        "elapsed": elapsed,
    }


@app.post("/api/deploy/cancel")
def deploy_cancel():
    """取消部署"""
    if not _deploy_state["running"]:
        return {"status": "not_running", "message": "没有正在运行的部署"}
    _deploy_state["cancelled"] = True
    return {"status": "cancelling", "message": "正在取消部署..."}


# 兼容旧API（同步部署，保留但不推荐）
@app.post("/api/deploy")
def deploy_legacy():
    """兼容旧版部署API（同步，可能超时）"""
    if not _deploy_lock.acquire(blocking=False):
        return {"status": "busy", "message": "已有部署任务正在运行"}
    thread = threading.Thread(target=_deploy_worker, daemon=True)
    thread.start()
    # 等待最多180秒
    for _ in range(180):
        if not _deploy_state["running"]:
            break
        time.sleep(1)
    return {
        "status": _deploy_state["result"] or "timeout",
        "stdout": "\n".join(_deploy_state["logs"][-50:]),
        "stderr": _deploy_state["error"],
    }


# ========== 数据模型 ==========
class PostData(BaseModel):
    title: str
    categories: list = []
    tags: list = []
    cover: str = ""
    content: str = ""


# ========== Front Matter 解析 ==========
def parse_front_matter(text):
    """解析YAML front-matter，返回(dict, content)"""
    match = re.match(r'^---\s*\n(.*?)\n---\s*\n?(.*)', text, re.DOTALL)
    if not match:
        return {}, text

    fm_text = match.group(1)
    content = match.group(2)
    fm = {}
    current_key = None
    current_list = []

    for line in fm_text.split('\n'):
        if line.startswith('  - ') and current_key:
            current_list.append(line[4:].strip())
        elif ':' in line and not line.startswith(' '):
            if current_key and current_list:
                fm[current_key] = current_list
                current_list = []
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()
            if value:
                fm[key] = value
                current_key = None
            else:
                current_key = key
                current_list = []

    if current_key and current_list:
        fm[current_key] = current_list

    # 后处理：兼容各种格式
    # 1. category 单数 -> categories 数组
    if 'category' in fm and 'categories' not in fm:
        fm['categories'] = _parse_list_value(fm['category'])
    elif 'categories' in fm:
        fm['categories'] = _parse_list_value(fm['categories'])

    # 2. tags 字符串 -> 数组
    if 'tags' in fm:
        fm['tags'] = _parse_list_value(fm['tags'])

    return fm, content


def _parse_list_value(value):
    """把各种格式的列表值统一转成数组"""
    if isinstance(value, list):
        return value
    if not isinstance(value, str):
        return [str(value)] if value else []

    s = value.strip()
    # 去掉首尾引号
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        s = s[1:-1].strip()
    # 去掉首尾方括号
    if s.startswith('[') and s.endswith(']'):
        s = s[1:-1].strip()
    # 按逗号分割
    if not s:
        return []
    items = [item.strip().strip('"\'') for item in s.split(',')]
    return [item for item in items if item]


def build_front_matter(fm):
    """构建YAML front-matter"""
    lines = ['---']
    for key, value in fm.items():
        if isinstance(value, list):
            if value:
                lines.append(f'{key}:')
                for item in value:
                    lines.append(f'  - {item}')
        else:
            lines.append(f'{key}: {value}')
    lines.append('---')
    lines.append('')
    return '\n'.join(lines)


# ========== API 路由 ==========
@app.get("/api/posts")
def list_posts(category: str = "", tag: str = "", keyword: str = "", sort: str = "date_desc"):
    """获取文章列表，支持筛选和排序
    sort: date_desc=时间降序(默认) / date_asc=时间升序 / title=标题排序
    """
    posts = []
    for md in POSTS_DIR.glob("*.md"):
        content = md.read_text(encoding="utf-8")
        fm, body = parse_front_matter(content)

        # 筛选
        if category and category not in fm.get("categories", []):
            continue
        if tag and tag not in fm.get("tags", []):
            continue
        if keyword:
            title = fm.get("title", "")
            if keyword.lower() not in title.lower() and keyword.lower() not in body[:500].lower():
                continue

        # 摘要
        excerpt = re.sub(r'[#*`>\-\[\]()]', '', body)[:150].replace('\n', ' ').strip()

        posts.append({
            "filename": md.name,
            "title": fm.get("title", md.stem),
            "date": fm.get("date", ""),
            "categories": fm.get("categories", []),
            "tags": fm.get("tags", []),
            "cover": fm.get("cover", ""),
            "excerpt": excerpt,
        })

    # 排序
    if sort == "date_asc":
        posts.sort(key=lambda p: p.get("date", ""))
    elif sort == "title":
        posts.sort(key=lambda p: p.get("title", "").lower())
    else:  # date_desc 默认
        posts.sort(key=lambda p: p.get("date", ""), reverse=True)

    return posts


@app.get("/api/posts/{filename}")
def get_post(filename: str):
    """获取单篇文章"""
    md = POSTS_DIR / filename
    if not md.exists():
        raise HTTPException(404, "文章不存在")
    content = md.read_text(encoding="utf-8")
    fm, body = parse_front_matter(content)
    return {
        "filename": filename,
        "title": fm.get("title", ""),
        "date": fm.get("date", ""),
        "categories": fm.get("categories", []),
        "tags": fm.get("tags", []),
        "cover": fm.get("cover", ""),
        "content": body,
    }


@app.post("/api/posts")
def create_post(post: PostData):
    """新建文章"""
    date_str = datetime.now().strftime("%Y-%m-%d")
    safe_title = re.sub(r'[^\w\u4e00-\u9fa5]+', '-', post.title).strip('-')[:60]
    filename = f"{date_str}-{safe_title}.md"

    fm = {
        "title": post.title,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "categories": post.categories,
        "tags": post.tags,
    }
    if post.cover:
        fm["cover"] = post.cover

    content = build_front_matter(fm) + post.content
    (POSTS_DIR / filename).write_text(content, encoding="utf-8")

    # 自动推送到远端
    github_path = f"source/_posts/{filename}"
    ok, msg = push_single_file(github_path, content, f"🐱 新建文章: {post.title}")
    return {"filename": filename, "status": "created", "synced": ok, "sync_msg": msg}


@app.put("/api/posts/{filename}")
def update_post(filename: str, post: PostData):
    """更新文章"""
    md = POSTS_DIR / filename
    if not md.exists():
        raise HTTPException(404, "文章不存在")

    # 保留原日期
    old_content = md.read_text(encoding="utf-8")
    old_fm, _ = parse_front_matter(old_content)

    fm = {
        "title": post.title,
        "date": old_fm.get("date", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        "categories": post.categories,
        "tags": post.tags,
    }
    if post.cover:
        fm["cover"] = post.cover

    content = build_front_matter(fm) + post.content
    md.write_text(content, encoding="utf-8")

    # 自动推送到远端
    github_path = f"source/_posts/{filename}"
    ok, msg = push_single_file(github_path, content, f"🐱 更新文章: {post.title}")
    return {"filename": filename, "status": "updated", "synced": ok, "sync_msg": msg}


@app.delete("/api/posts/{filename}")
def delete_post(filename: str):
    """删除文章（同时删除远端）"""
    md = POSTS_DIR / filename
    if not md.exists():
        raise HTTPException(404, "文章不存在")
    md.unlink()

    # 同步删除远端文件
    try:
        github_path = f"source/_posts/{filename}"
        # 获取当前commit和tree
        ref = requests.get(f"{GITHUB_API}/repos/{OWNER}/{REPO}/git/ref/heads/{BRANCH}",
                           headers=GITHUB_HEADERS, timeout=30)
        ref.raise_for_status()
        commit_sha = ref.json()['object']['sha']
        commit = requests.get(f"{GITHUB_API}/repos/{OWNER}/{REPO}/git/commits/{commit_sha}",
                              headers=GITHUB_HEADERS, timeout=30)
        commit.raise_for_status()
        tree_sha = commit.json()['tree']['sha']

        # 创建tree，sha设为null表示删除
        r = requests.post(f"{GITHUB_API}/repos/{OWNER}/{REPO}/git/trees",
                          headers=GITHUB_HEADERS,
                          json={"base_tree": tree_sha, "tree": [{
                              "path": github_path, "mode": "100644", "type": "blob", "sha": None,
                          }]},
                          timeout=30)
        r.raise_for_status()
        new_tree_sha = r.json()["sha"]

        # 创建commit
        r = requests.post(f"{GITHUB_API}/repos/{OWNER}/{REPO}/git/commits",
                          headers=GITHUB_HEADERS,
                          json={"message": f"🐱 删除文章: {filename}", "tree": new_tree_sha, "parents": [commit_sha]},
                          timeout=30)
        r.raise_for_status()
        new_commit_sha = r.json()["sha"]

        # 更新引用
        r = requests.patch(f"{GITHUB_API}/repos/{OWNER}/{REPO}/git/refs/heads/{BRANCH}",
                           headers=GITHUB_HEADERS,
                           json={"sha": new_commit_sha, "force": False},
                           timeout=30)
        r.raise_for_status()
        return {"status": "deleted", "synced": True}
    except Exception as e:
        return {"status": "deleted", "synced": False, "sync_error": str(e)[:200]}


@app.get("/api/categories")
def list_categories():
    """获取所有分类及文章数"""
    cat_count = {}
    for md in POSTS_DIR.glob("*.md"):
        content = md.read_text(encoding="utf-8")
        fm, _ = parse_front_matter(content)
        for c in fm.get("categories", []):
            cat_count[c] = cat_count.get(c, 0) + 1
    return [{"name": k, "count": v} for k, v in sorted(cat_count.items())]


@app.get("/api/tags")
def list_tags():
    """获取所有标签及文章数"""
    tag_count = {}
    for md in POSTS_DIR.glob("*.md"):
        content = md.read_text(encoding="utf-8")
        fm, _ = parse_front_matter(content)
        for t in fm.get("tags", []):
            tag_count[t] = tag_count.get(t, 0) + 1
    return [{"name": k, "count": v} for k, v in sorted(tag_count.items())]


# ========== 分类/标签管理 ==========
class RenameRequest(BaseModel):
    old_name: str
    new_name: str


class MergeRequest(BaseModel):
    from_name: str
    to_name: str


def _update_all_posts(transform_fn):
    """遍历所有文章，用transform_fn(fm)修改front-matter，返回修改的文章数"""
    count = 0
    for md in POSTS_DIR.glob("*.md"):
        content = md.read_text(encoding="utf-8")
        fm, body = parse_front_matter(content)
        original_cats = list(fm.get("categories", []))
        original_tags = list(fm.get("tags", []))

        transform_fn(fm)

        # 只有真正修改了才写回
        if fm.get("categories", []) != original_cats or fm.get("tags", []) != original_tags:
            # 保留原始front-matter的其他字段，只更新categories/tags
            new_content = build_front_matter(fm) + body
            md.write_text(new_content, encoding="utf-8")
            count += 1
    return count


@app.post("/api/categories/rename")
def rename_category(req: RenameRequest):
    """重命名分类（批量修改所有文章的category）"""
    if not req.old_name or not req.new_name:
        raise HTTPException(400, "分类名不能为空")
    if req.old_name == req.new_name:
        return {"updated": 0, "message": "新旧名称相同"}

    def transform(fm):
        cats = fm.get("categories", [])
        fm["categories"] = [req.new_name if c == req.old_name else c for c in cats]

    count = _update_all_posts(transform)
    return {"updated": count, "message": f"已将 {count} 篇文章的分类从「{req.old_name}」改为「{req.new_name}」"}


@app.post("/api/categories/merge")
def merge_category(req: MergeRequest):
    """合并分类（把from_name分类的文章都改成to_name）"""
    if not req.from_name or not req.to_name:
        raise HTTPException(400, "分类名不能为空")
    if req.from_name == req.to_name:
        return {"updated": 0, "message": "两个分类相同"}

    def transform(fm):
        cats = fm.get("categories", [])
        # 把from改成to，并去重
        new_cats = []
        for c in cats:
            nc = req.to_name if c == req.from_name else c
            if nc not in new_cats:
                new_cats.append(nc)
        fm["categories"] = new_cats

    count = _update_all_posts(transform)
    return {"updated": count, "message": f"已将 {count} 篇文章从「{req.from_name}」合并到「{req.to_name}」"}


@app.delete("/api/categories/{name}")
def delete_category(name: str):
    """删除分类（从所有文章中移除该分类）"""
    if not name:
        raise HTTPException(400, "分类名不能为空")

    def transform(fm):
        fm["categories"] = [c for c in fm.get("categories", []) if c != name]

    count = _update_all_posts(transform)
    return {"updated": count, "message": f"已从 {count} 篇文章中移除分类「{name}」"}


@app.post("/api/tags/rename")
def rename_tag(req: RenameRequest):
    """重命名标签"""
    if not req.old_name or not req.new_name:
        raise HTTPException(400, "标签名不能为空")
    if req.old_name == req.new_name:
        return {"updated": 0, "message": "新旧名称相同"}

    def transform(fm):
        tags = fm.get("tags", [])
        fm["tags"] = [req.new_name if t == req.old_name else t for t in tags]

    count = _update_all_posts(transform)
    return {"updated": count, "message": f"已将 {count} 篇文章的标签从「{req.old_name}」改为「{req.new_name}」"}


@app.post("/api/tags/merge")
def merge_tag(req: MergeRequest):
    """合并标签"""
    if not req.from_name or not req.to_name:
        raise HTTPException(400, "标签名不能为空")
    if req.from_name == req.to_name:
        return {"updated": 0, "message": "两个标签相同"}

    def transform(fm):
        tags = fm.get("tags", [])
        new_tags = []
        for t in tags:
            nt = req.to_name if t == req.from_name else t
            if nt not in new_tags:
                new_tags.append(nt)
        fm["tags"] = new_tags

    count = _update_all_posts(transform)
    return {"updated": count, "message": f"已将 {count} 篇文章从「{req.from_name}」合并到「{req.to_name}」"}


@app.delete("/api/tags/{name}")
def delete_tag(name: str):
    """删除标签（从所有文章中移除该标签）"""
    if not name:
        raise HTTPException(400, "标签名不能为空")

    def transform(fm):
        fm["tags"] = [t for t in fm.get("tags", []) if t != name]

    count = _update_all_posts(transform)
    return {"updated": count, "message": f"已从 {count} 篇文章中移除标签「{name}」"}


@app.get("/api/stats")
def stats():
    """统计信息"""
    posts = list(POSTS_DIR.glob("*.md"))
    cats = set()
    tags = set()
    total_chars = 0
    for md in posts:
        content = md.read_text(encoding="utf-8")
        fm, body = parse_front_matter(content)
        for c in fm.get("categories", []):
            cats.add(c)
        for t in fm.get("tags", []):
            tags.add(t)
        total_chars += len(body)
    return {
        "total_posts": len(posts),
        "total_categories": len(cats),
        "total_tags": len(tags),
        "total_chars": total_chars,
    }


# ========== 站点设置 ==========
MAIN_CONFIG = BLOG_ROOT / "_config.yml"
THEME_CONFIG = BLOG_ROOT / "_config.butterfly.yml"


def _read_yaml_value(filepath, key_path):
    """从YAML文件中读取嵌套配置项的值（用正则，保留注释）
    key_path: 如 'title', 'aside.card_author.description'
    """
    if not filepath.exists():
        return ""
    content = filepath.read_text(encoding="utf-8")
    keys = key_path.split('.')

    # 简单顶层key
    if len(keys) == 1:
        pattern = rf'^{re.escape(keys[0])}:\s*(.+?)\s*$'
        match = re.search(pattern, content, re.MULTILINE)
        if match:
            val = match.group(1).strip()
            # 去掉引号
            if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                val = val[1:-1]
            return val
        return ""

    # 嵌套key：逐行缩进匹配
    lines = content.split('\n')
    current_indent = 0
    found_keys = 0
    for i, line in enumerate(lines):
        stripped = line.lstrip()
        if not stripped or stripped.startswith('#'):
            continue
        indent = len(line) - len(stripped)

        if found_keys < len(keys) - 1:
            # 匹配中间的key
            if stripped.startswith(f"{keys[found_keys]}:") and indent == current_indent:
                found_keys += 1
                current_indent = indent + 2
            elif found_keys > 0 and indent < current_indent - 2:
                break
        else:
            # 匹配最后一个key
            if stripped.startswith(f"{keys[-1]}:") and indent == current_indent:
                val = stripped[len(keys[-1]) + 1:].strip()
                if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                    val = val[1:-1]
                return val
            # 遇到更高级别的key，说明已经出了父key的范围
            if indent < current_indent:
                break
    return ""


def _write_yaml_value(filepath, key_path, new_value):
    """写入YAML配置项的值（用正则替换，保留注释和其他内容）"""
    if not filepath.exists():
        return False
    content = filepath.read_text(encoding="utf-8")
    keys = key_path.split('.')

    # 简单顶层key
    if len(keys) == 1:
        pattern = rf'^({re.escape(keys[0])}:\s*).+$'
        new_content = re.sub(pattern, rf'\g<1>{new_value}', content, flags=re.MULTILINE)
        if new_content != content:
            filepath.write_text(new_content, encoding="utf-8")
            return True
        return False

    # 嵌套key
    lines = content.split('\n')
    current_indent = 0
    found_keys = 0
    for i, line in enumerate(lines):
        stripped = line.lstrip()
        if not stripped or stripped.startswith('#'):
            continue
        indent = len(line) - len(stripped)

        if found_keys < len(keys) - 1:
            # 还在找父级key
            if stripped.startswith(f"{keys[found_keys]}:") and indent == current_indent:
                found_keys += 1
                current_indent = indent + 2
            # 如果遇到更高级别的key，说明父key不存在
            elif found_keys > 0 and indent < current_indent - 2:
                break
        else:
            # 已经找到父key，正在找子key
            if stripped.startswith(f"{keys[-1]}:") and indent == current_indent:
                lines[i] = f"{' ' * indent}{keys[-1]}: {new_value}"
                filepath.write_text('\n'.join(lines), encoding="utf-8")
                return True
            # 遇到更高级别的key，说明已经出了父key的范围
            if indent < current_indent:
                break
    return False


class SiteSettings(BaseModel):
    # 基本信息
    title: str = ""
    subtitle: str = ""
    description: str = ""
    author: str = ""
    language: str = ""
    per_page: int = 10
    # 主题设置
    avatar: str = ""
    author_description: str = ""
    follow_icon: str = ""
    follow_text: str = ""
    follow_link: str = ""
    announcement: str = ""


@app.get("/api/settings")
def get_settings():
    """读取站点设置"""
    # 首页分页用 index_generator.per_page，优先读这个
    index_per_page = _read_yaml_value(MAIN_CONFIG, "index_generator.per_page")
    global_per_page = _read_yaml_value(MAIN_CONFIG, "per_page")
    per_page_val = index_per_page or global_per_page or "10"
    return {
        "title": _read_yaml_value(MAIN_CONFIG, "title"),
        "subtitle": _read_yaml_value(MAIN_CONFIG, "subtitle"),
        "description": _read_yaml_value(MAIN_CONFIG, "description"),
        "author": _read_yaml_value(MAIN_CONFIG, "author"),
        "language": _read_yaml_value(MAIN_CONFIG, "language"),
        "per_page": int(per_page_val),
        "avatar": _read_yaml_value(THEME_CONFIG, "avatar.img"),
        "author_description": _read_yaml_value(THEME_CONFIG, "aside.card_author.description"),
        "follow_icon": _read_yaml_value(THEME_CONFIG, "aside.card_author.button.icon"),
        "follow_text": _read_yaml_value(THEME_CONFIG, "aside.card_author.button.text"),
        "follow_link": _read_yaml_value(THEME_CONFIG, "aside.card_author.button.link"),
        "announcement": _read_yaml_value(THEME_CONFIG, "aside.card_announcement.content"),
    }


@app.post("/api/settings")
def save_settings(settings: SiteSettings):
    """保存站点设置"""
    results = {}
    # 主配置
    results["title"] = _write_yaml_value(MAIN_CONFIG, "title", settings.title)
    results["subtitle"] = _write_yaml_value(MAIN_CONFIG, "subtitle", settings.subtitle)
    results["description"] = _write_yaml_value(MAIN_CONFIG, "description", settings.description)
    results["author"] = _write_yaml_value(MAIN_CONFIG, "author", settings.author)
    results["language"] = _write_yaml_value(MAIN_CONFIG, "language", settings.language)
    # 分页：同时改首页分页(index_generator.per_page)和全局分页(per_page)
    results["per_page"] = _write_yaml_value(MAIN_CONFIG, "index_generator.per_page", str(settings.per_page))
    _write_yaml_value(MAIN_CONFIG, "per_page", str(settings.per_page))
    # 主题配置
    results["avatar"] = _write_yaml_value(THEME_CONFIG, "avatar.img", settings.avatar)
    results["author_description"] = _write_yaml_value(THEME_CONFIG, "aside.card_author.description", settings.author_description)
    results["follow_icon"] = _write_yaml_value(THEME_CONFIG, "aside.card_author.button.icon", settings.follow_icon)
    results["follow_text"] = _write_yaml_value(THEME_CONFIG, "aside.card_author.button.text", settings.follow_text)
    results["follow_link"] = _write_yaml_value(THEME_CONFIG, "aside.card_author.button.link", settings.follow_link)
    results["announcement"] = _write_yaml_value(THEME_CONFIG, "aside.card_announcement.content", settings.announcement)

    success_count = sum(1 for v in results.values() if v)

    # 自动推送到远端
    sync_results = {}
    if results.get("title") or results.get("subtitle") or results.get("description") or results.get("author") or results.get("language") or results.get("per_page"):
        main_content = MAIN_CONFIG.read_text(encoding="utf-8")
        ok, msg = push_single_file("_config.yml", main_content, "🐱 更新站点配置")
        sync_results["_config.yml"] = ok
    if results.get("avatar") or results.get("author_description") or results.get("follow_icon") or results.get("follow_text") or results.get("follow_link") or results.get("announcement"):
        theme_content = THEME_CONFIG.read_text(encoding="utf-8")
        ok, msg = push_single_file("_config.butterfly.yml", theme_content, "🐱 更新主题配置")
        sync_results["_config.butterfly.yml"] = ok

    return {
        "status": "success",
        "updated": success_count,
        "total": len(results),
        "details": results,
        "synced": sync_results,
        "message": f"已保存 {success_count}/{len(results)} 项设置，已同步到远端"
    }


# ========== 自动同步开关 ==========
@app.get("/api/auto-sync")
def get_auto_sync_status():
    """获取自动同步状态"""
    return {"enabled": AUTO_SYNC_ENABLED}


@app.post("/api/auto-sync")
def set_auto_sync_status(data: dict):
    """设置自动同步状态"""
    global AUTO_SYNC_ENABLED
    AUTO_SYNC_ENABLED = data.get("enabled", True)
    return {"enabled": AUTO_SYNC_ENABLED, "message": "自动同步已开启" if AUTO_SYNC_ENABLED else "自动同步已关闭，文件仅保存在本地"}


# ========== 图片上传 ==========
IMG_DIR = BLOG_ROOT / "source" / "img"
ALLOWED_EXT = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg'}


@app.post("/api/upload")
async def upload_image(file: UploadFile = File(...)):
    """上传图片到 source/img/，返回相对路径"""
    # 检查文件类型
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(400, f"不支持的格式: {ext}，支持: {', '.join(ALLOWED_EXT)}")

    # 检查文件大小（最大10MB）
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(400, "文件过大，最大10MB")

    # 确保目录存在
    IMG_DIR.mkdir(parents=True, exist_ok=True)

    # 生成唯一文件名
    unique_name = f"{uuid.uuid4().hex[:8]}_{Path(file.filename).stem}{ext}"
    save_path = IMG_DIR / unique_name
    save_path.write_bytes(content)

    # 返回相对路径（Hexo中用 /img/xxx.png 引用）
    result = {
        "status": "success",
        "url": f"/img/{unique_name}",
        "filename": unique_name,
        "size": len(content),
        "message": "上传成功"
    }

    # 自动推送到远端
    github_path = f"source/img/{unique_name}"
    # 二进制文件需要用base64编码后作为字符串传入
    content_b64 = base64.b64encode(content).decode("ascii")
    # push_single_file需要文本内容，图片用base64会有问题
    # 改用直接调用GitHub API的方式推送二进制文件
    try:
        # 获取当前commit
        ref = requests.get(f"{GITHUB_API}/repos/{OWNER}/{REPO}/git/ref/heads/{BRANCH}",
                           headers=GITHUB_HEADERS, timeout=30)
        ref.raise_for_status()
        commit_sha = ref.json()['object']['sha']
        commit = requests.get(f"{GITHUB_API}/repos/{OWNER}/{REPO}/git/commits/{commit_sha}",
                              headers=GITHUB_HEADERS, timeout=30)
        commit.raise_for_status()
        tree_sha = commit.json()['tree']['sha']

        # 创建blob（二进制用base64）
        r = requests.post(f"{GITHUB_API}/repos/{OWNER}/{REPO}/git/blobs",
                          headers=GITHUB_HEADERS,
                          json={"content": content_b64, "encoding": "base64"},
                          timeout=30)
        r.raise_for_status()
        blob_sha = r.json()["sha"]

        # 创建tree
        r = requests.post(f"{GITHUB_API}/repos/{OWNER}/{REPO}/git/trees",
                          headers=GITHUB_HEADERS,
                          json={"base_tree": tree_sha, "tree": [{
                              "path": github_path, "mode": "100644", "type": "blob", "sha": blob_sha,
                          }]},
                          timeout=30)
        r.raise_for_status()
        new_tree_sha = r.json()["sha"]

        # 创建commit
        r = requests.post(f"{GITHUB_API}/repos/{OWNER}/{REPO}/git/commits",
                          headers=GITHUB_HEADERS,
                          json={"message": f"🐱 上传图片: {unique_name}", "tree": new_tree_sha, "parents": [commit_sha]},
                          timeout=30)
        r.raise_for_status()
        new_commit_sha = r.json()["sha"]

        # 更新引用
        r = requests.patch(f"{GITHUB_API}/repos/{OWNER}/{REPO}/git/refs/heads/{BRANCH}",
                           headers=GITHUB_HEADERS,
                           json={"sha": new_commit_sha, "force": False},
                           timeout=30)
        r.raise_for_status()
        result["synced"] = True
        result["message"] = "上传成功，已同步到远端"
    except Exception as e:
        result["synced"] = False
        result["sync_error"] = str(e)[:200]

    return result


@app.get("/api/images")
def list_images():
    """列出已上传的图片"""
    if not IMG_DIR.exists():
        return {"images": []}
    images = []
    for f in sorted(IMG_DIR.iterdir()):
        if f.is_file() and f.suffix.lower() in ALLOWED_EXT:
            images.append({
                "url": f"/img/{f.name}",
                "name": f.name,
                "size": f.stat().st_size,
            })
    return {"images": images}


@app.delete("/api/images")
def delete_image(filename: str):
    """删除图片（本地+远端），filename用query参数传递，避免中文编码问题"""
    # 安全检查：防止路径遍历
    if not filename or '..' in filename or '/' in filename or '\\' in filename:
        raise HTTPException(400, "非法文件名")
    if Path(filename).suffix.lower() not in ALLOWED_EXT:
        raise HTTPException(400, "不支持的文件类型")

    img_path = IMG_DIR / filename
    if not img_path.exists():
        raise HTTPException(404, "图片不存在")

    # 删除本地
    img_path.unlink()

    # 同步删除远端
    try:
        github_path = f"source/img/{filename}"
        ref = requests.get(f"{GITHUB_API}/repos/{OWNER}/{REPO}/git/ref/heads/{BRANCH}",
                           headers=GITHUB_HEADERS, timeout=30)
        ref.raise_for_status()
        commit_sha = ref.json()['object']['sha']
        commit = requests.get(f"{GITHUB_API}/repos/{OWNER}/{REPO}/git/commits/{commit_sha}",
                              headers=GITHUB_HEADERS, timeout=30)
        commit.raise_for_status()
        tree_sha = commit.json()['tree']['sha']

        r = requests.post(f"{GITHUB_API}/repos/{OWNER}/{REPO}/git/trees",
                          headers=GITHUB_HEADERS,
                          json={"base_tree": tree_sha, "tree": [{
                              "path": github_path, "mode": "100644", "type": "blob", "sha": None,
                          }]},
                          timeout=30)
        r.raise_for_status()
        new_tree_sha = r.json()["sha"]

        r = requests.post(f"{GITHUB_API}/repos/{OWNER}/{REPO}/git/commits",
                          headers=GITHUB_HEADERS,
                          json={"message": f"🐱 删除图片: {filename}", "tree": new_tree_sha, "parents": [commit_sha]},
                          timeout=30)
        r.raise_for_status()
        new_commit_sha = r.json()["sha"]

        r = requests.patch(f"{GITHUB_API}/repos/{OWNER}/{REPO}/git/refs/heads/{BRANCH}",
                           headers=GITHUB_HEADERS,
                           json={"sha": new_commit_sha, "force": False},
                           timeout=30)
        r.raise_for_status()
        return {"status": "deleted", "synced": True, "message": "图片已删除，已同步到远端"}
    except Exception as e:
        return {"status": "deleted", "synced": False, "sync_error": str(e)[:200], "message": "本地已删除，远端同步失败"}


# ========== 静态文件 ==========
app.mount("/static", StaticFiles(directory=ADMIN_DIR / "static"), name="static")
# 挂载博客图片目录，供后台预览
IMG_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/img", StaticFiles(directory=IMG_DIR), name="blog-img")


@app.get("/")
def index():
    return FileResponse(ADMIN_DIR / "static" / "index.html")


if __name__ == "__main__":
    import uvicorn
    print("🐱 喵喵小码 - 文章管理后台启动中...")
    print("📝 访问地址: http://localhost:5000")
    uvicorn.run(app, host="127.0.0.1", port=5000)
