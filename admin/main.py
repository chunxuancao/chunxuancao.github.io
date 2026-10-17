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
import subprocess
import threading
from datetime import datetime

app = FastAPI(title="喵喵小码 - 文章管理后台")

BLOG_ROOT = Path(__file__).parent.parent
POSTS_DIR = BLOG_ROOT / "source" / "_posts"
ADMIN_DIR = Path(__file__).parent

# 部署锁，防止并发部署
_deploy_lock = threading.Lock()
_deploy_running = False


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


@app.post("/api/deploy")
def deploy():
    """一键部署到GitHub"""
    global _deploy_running
    # 检查是否已有部署在运行
    if not _deploy_lock.acquire(blocking=False):
        return {
            "status": "busy",
            "message": "已有部署任务正在运行，请稍候..."
        }
    _deploy_running = True
    try:
        print("🚀 开始部署到 GitHub...")
        result = subprocess.run(
            ["python", str(BLOG_ROOT / "tools" / "push_to_github.py")],
            capture_output=True, text=True, cwd=str(BLOG_ROOT), timeout=180
        )
        print(f"部署完成，返回码: {result.returncode}")
        stdout = result.stdout or ''
        stderr = result.stderr or ''
        # 截取最后3000字符，避免返回太大
        if len(stdout) > 3000:
            stdout = '...(省略前面部分)...\n' + stdout[-3000:]
        return {
            "status": "success" if result.returncode == 0 else "failed",
            "returncode": result.returncode,
            "stdout": stdout,
            "stderr": stderr[-1000:] if stderr else '',
        }
    except subprocess.TimeoutExpired:
        print("部署超时")
        return {"status": "timeout", "message": "部署超时（超过3分钟），请稍后查看GitHub Actions状态"}
    except Exception as e:
        print(f"部署出错: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        _deploy_running = False
        _deploy_lock.release()


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
