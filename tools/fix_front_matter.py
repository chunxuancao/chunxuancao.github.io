#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批量修复文章front-matter格式：
1. tags: "[a, b, c]" 字符串 -> 标准YAML列表
2. category: 单数 -> categories: 数组
"""
import re
from pathlib import Path

POSTS_DIR = Path(__file__).parent.parent / "source" / "_posts"


def fix_front_matter(content):
    """修复单篇文章的front-matter"""
    match = re.match(r'^---\s*\n(.*?)\n---\s*\n?(.*)', content, re.DOTALL)
    if not match:
        return content, False

    fm_text = match.group(1)
    body = match.group(2)
    lines = fm_text.split('\n')
    new_lines = []
    changed = False
    i = 0

    while i < len(lines):
        line = lines[i]

        # 处理 tags: "[a, b, c]" 或 tags: [a, b, c] 字符串格式
        tags_match = re.match(r'^tags:\s*["\']?\[(.*?)\]["\']?\s*$', line)
        if tags_match:
            tags_str = tags_match.group(1).strip()
            if tags_str:
                tags = [t.strip().strip('"\'') for t in tags_str.split(',') if t.strip()]
            else:
                tags = []
            new_lines.append('tags:')
            for tag in tags:
                new_lines.append(f'  - {tag}')
            changed = True
            i += 1
            continue

        # 处理 category: xxx 单数 -> categories
        cat_match = re.match(r'^category:\s*(.+?)\s*$', line)
        if cat_match and not line.startswith('categories:'):
            cat_val = cat_match.group(1).strip().strip('"\'')
            new_lines.append('categories:')
            new_lines.append(f'  - {cat_val}')
            changed = True
            i += 1
            continue

        # 处理已经是 categories: 字符串格式
        cats_match = re.match(r'^categories:\s*["\']?\[(.*?)\]["\']?\s*$', line)
        if cats_match:
            cats_str = cats_match.group(1).strip()
            if cats_str:
                cats = [c.strip().strip('"\'') for c in cats_str.split(',') if c.strip()]
            else:
                cats = []
            new_lines.append('categories:')
            for cat in cats:
                new_lines.append(f'  - {cat}')
            changed = True
            i += 1
            continue

        new_lines.append(line)
        i += 1

    if not changed:
        return content, False

    new_fm = '\n'.join(new_lines)
    return f'---\n{new_fm}\n---\n{body}', True


def main():
    posts = list(POSTS_DIR.glob("*.md"))
    fixed_count = 0
    print(f"共找到 {len(posts)} 篇文章")

    for md in sorted(posts):
        content = md.read_text(encoding="utf-8")
        new_content, changed = fix_front_matter(content)
        if changed:
            md.write_text(new_content, encoding="utf-8")
            fixed_count += 1
            print(f"  修复: {md.name}")

    print(f"\n完成！共修复 {fixed_count}/{len(posts)} 篇文章")


if __name__ == "__main__":
    main()
