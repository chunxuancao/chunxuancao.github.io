#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
喵喵小码 - 文章管理后台
FastAPI + 静态前端
"""
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pathlib import Path
import re
import base64
import threading
import sys
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


def _deploy_worker():
    """部署工作线程"""
    global _deploy_state
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
        _deploy_log(f"待推送文件: {len(files_to_push)} 个")

        if _deploy_check_cancel():
            raise _DeployCancelled()

        # 阶段3: 创建blobs (10%-70%)
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

        # 阶段3.5: 同步删除远端多余文件 (72%)
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
    """启动部署（异步）"""
    if not _deploy_lock.acquire(blocking=False):
        return {"status": "busy", "message": "已有部署任务正在运行"}
    # 启动工作线程
    thread = threading.Thread(target=_deploy_worker, daemon=True)
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
def list_posts(category: str = "", tag: str = "", keyword: str = ""):
    """获取文章列表，支持筛选"""
    posts = []
    for md in sorted(POSTS_DIR.glob("*.md"), reverse=True):
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
    return {"filename": filename, "status": "created"}


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
    return {"filename": filename, "status": "updated"}


@app.delete("/api/posts/{filename}")
def delete_post(filename: str):
    """删除文章"""
    md = POSTS_DIR / filename
    if not md.exists():
        raise HTTPException(404, "文章不存在")
    md.unlink()
    return {"status": "deleted"}


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


# ========== 静态文件 ==========
app.mount("/static", StaticFiles(directory=ADMIN_DIR / "static"), name="static")


@app.get("/")
def index():
    return FileResponse(ADMIN_DIR / "static" / "index.html")


if __name__ == "__main__":
    import uvicorn
    print("🐱 喵喵小码 - 文章管理后台启动中...")
    print("📝 访问地址: http://localhost:5000")
    uvicorn.run(app, host="127.0.0.1", port=5000)
