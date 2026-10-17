#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批量推送文件到GitHub（用git blobs + trees + commits API，一次commit）"""
import base64
import sys
from pathlib import Path

import requests

# 从本地配置导入（不推送到GitHub）
sys.path.insert(0, str(Path(__file__).parent))
from local_config import GITHUB_TOKEN as TOKEN, GITHUB_OWNER as OWNER, GITHUB_REPO as REPO, GITHUB_BRANCH as BRANCH

API = "https://api.github.com"

HEADERS = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

BLOG_ROOT = Path(__file__).parent.parent

# 不推送的文件（包含敏感信息或临时文件）
EXCLUDE_FILES = {
    "tools/local_config.py",
    "tools/debug_push.py",
    "tools/test_api.py",
    "tools/test_fix.py",
    "tools/test_final.py",
}


def api_get(url):
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.json()


def api_post(url, data):
    r = requests.post(url, headers=HEADERS, json=data, timeout=30)
    if r.status_code != 201:
        raise Exception(f"HTTP {r.status_code}: {r.text[:300]}")
    return r.json()


def api_patch(url, data):
    r = requests.patch(url, headers=HEADERS, json=data, timeout=30)
    r.raise_for_status()
    return r.json()


def add_file(files_list, rel_path, abs_path):
    """添加文件到推送列表，跳过空文件和排除列表"""
    if rel_path in EXCLUDE_FILES:
        return
    if not abs_path.exists():
        return
    content = abs_path.read_text(encoding="utf-8")
    if not content or len(content.strip()) == 0:
        print(f"  ⚠️  跳过空文件: {rel_path}")
        return
    files_list.append({
        "path": rel_path,
        "content": content,
    })


def main():
    # 1. 获取当前分支最新commit
    print("获取当前分支信息...")
    ref = api_get(f"{API}/repos/{OWNER}/{REPO}/git/ref/heads/{BRANCH}")
    commit_sha = ref["object"]["sha"]
    print(f"  当前commit: {commit_sha[:8]}")

    commit = api_get(f"{API}/repos/{OWNER}/{REPO}/git/commits/{commit_sha}")
    tree_sha = commit["tree"]["sha"]
    print(f"  当前tree: {tree_sha[:8]}")

    # 2. 收集要推送的文件
    files_to_push = []

    # 猫系主题CSS + JS
    add_file(files_to_push, "source/css/cat-theme.css",
             BLOG_ROOT / "source" / "css" / "cat-theme.css")
    add_file(files_to_push, "source/js/cat-theme.js",
             BLOG_ROOT / "source" / "js" / "cat-theme.js")

    # 主题配置
    add_file(files_to_push, "_config.butterfly.yml",
             BLOG_ROOT / "_config.butterfly.yml")

    # 所有文章md
    posts_dir = BLOG_ROOT / "source" / "_posts"
    for md in sorted(posts_dir.glob("*.md")):
        add_file(files_to_push, f"source/_posts/{md.name}", md)

    # 工具脚本（tools目录下所有.py，排除敏感文件）
    tools_dir = BLOG_ROOT / "tools"
    if tools_dir.exists():
        for py in sorted(tools_dir.glob("*.py")):
            add_file(files_to_push, f"tools/{py.name}", py)

    # 管理后台（admin目录）
    admin_dir = BLOG_ROOT / "admin"
    if admin_dir.exists():
        add_file(files_to_push, "admin/main.py", admin_dir / "main.py")
        add_file(files_to_push, "admin/start.py", admin_dir / "start.py")
        add_file(files_to_push, "admin/requirements.txt", admin_dir / "requirements.txt")
        add_file(files_to_push, "admin/static/index.html", admin_dir / "static" / "index.html")

    # 一键脚本
    for bat in ["start-blog.bat", "stop-blog.bat", "deploy-blog.bat", "start-admin.bat"]:
        add_file(files_to_push, bat, BLOG_ROOT / bat)

    print(f"  待推送文件: {len(files_to_push)} 个")

    # 3. 为每个文件创建blob
    print("创建blobs...")
    tree_items = []
    for i, f in enumerate(files_to_push, 1):
        try:
            content_b64 = base64.b64encode(f["content"].encode("utf-8")).decode("ascii")
            blob = api_post(f"{API}/repos/{OWNER}/{REPO}/git/blobs", {
                "content": content_b64,
                "encoding": "base64",
            })
            tree_items.append({
                "path": f["path"],
                "mode": "100644",
                "type": "blob",
                "sha": blob["sha"],
            })
            if i % 10 == 0:
                print(f"  {i}/{len(files_to_push)} blobs created")
        except Exception as e:
            print(f"  ❌ 文件失败: {f['path']} - {e}")
            raise

    print(f"  全部 {len(tree_items)} blobs created")

    # 4. 创建新tree
    print("创建新tree...")
    new_tree = api_post(f"{API}/repos/{OWNER}/{REPO}/git/trees", {
        "base_tree": tree_sha,
        "tree": tree_items,
    })
    new_tree_sha = new_tree["sha"]
    print(f"  新tree: {new_tree_sha[:8]}")

    # 5. 创建commit
    print("创建commit...")
    new_commit = api_post(f"{API}/repos/{OWNER}/{REPO}/git/commits", {
        "message": "🐱 文章管理后台 + 猫系主题优化 + 部署修复",
        "tree": new_tree_sha,
        "parents": [commit_sha],
    })
    new_commit_sha = new_commit["sha"]
    print(f"  新commit: {new_commit_sha[:8]}")

    # 6. 更新分支ref
    print("更新分支ref...")
    api_patch(f"{API}/repos/{OWNER}/{REPO}/git/refs/heads/{BRANCH}", {
        "sha": new_commit_sha,
        "force": False,
    })
    print("  ✅ 推送完成！")

    print(f"\n提交信息: 🐱 文章管理后台 + 猫系主题优化 + 部署修复")
    print(f"文件数量: {len(files_to_push)}")
    print(f"Commit: {new_commit_sha}")


if __name__ == "__main__":
    main()
