#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
喵喵小码 · 猫图封面自动生成器
==============================
功能：
  1. 扫描 source/_posts/ 下所有文章
  2. 从免费猫图API爬取一张猫图（cataas.com / TheCatAPI）
  3. 用PIL统一处理成猫系毛绒绒风格（深紫蓝滤镜 + 橙色边框 + 圆角）
  4. 保存到 source/images/cat-covers/
  5. 自动更新文章 front matter 中的 cover 字段

用法：
  python scripts/fetch-cat-covers.py           # 为所有没有cover的文章生成
  python scripts/fetch-cat-covers.py --force   # 强制重新生成所有
  python scripts/fetch-cat-covers.py --dry-run # 只预览不写入
"""

import os
import re
import sys
import time
import random
import hashlib
import requests
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

# ── 配置 ──────────────────────────────────────────────
BLOG_ROOT = Path(__file__).parent.parent
POSTS_DIR = BLOG_ROOT / "source" / "_posts"
OUTPUT_DIR = BLOG_ROOT / "source" / "images" / "cat-covers"

# 猫系主题色
CAT_BG = (26, 18, 40)        # 深紫蓝背景
CAT_ACCENT = (255, 157, 92)  # 橙色强调
CAT_ACCENT2 = (255, 185, 128)
CAT_FUR = (232, 133, 74)

# 图片尺寸（Hexo文章封面推荐比例）
COVER_WIDTH = 800
COVER_HEIGHT = 500

# 猫图API列表（按优先级，失败自动切换）
CAT_APIS = [
    # cataas.com - 完全免费无需key
    {"name": "cataas", "url": "https://cataas.com/cat?width={w}&height={h}", "json": False},
    # TheCatAPI - 免费无需key（有速率限制）
    {"name": "thecatapi", "url": "https://api.thecatapi.com/v1/images/search?limit=1", "json": True},
    # placekitten - 备用
    {"name": "placekitten", "url": "https://placekitten.com/{w}/{h}", "json": False},
]

# 分类对应的emoji（用于生成时加在图片上）
CATEGORY_EMOJI = {
    "反爬技巧": "🛡️",
    "JS逆向": "🔍",
    "环境配置": "⚙️",
    "接单经验": "💰",
    "工具推荐": "🧰",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "image/*,*/*;q=0.8",
}


# ── 工具函数 ──────────────────────────────────────────
def parse_front_matter(content):
    """解析Hexo front matter，返回(dict, body_start_pos)"""
    if not content.startswith("---"):
        return {}, 0
    end = content.find("---", 3)
    if end == -1:
        return {}, 0
    fm_text = content[3:end].strip()
    fm = {}
    current_key = None
    current_list = None
    for line in fm_text.split("\n"):
        if line.strip().startswith("#") or not line.strip():
            continue
        # 列表项
        if line.strip().startswith("- ") and current_key:
            if current_list is None:
                current_list = []
                fm[current_key] = current_list
            current_list.append(line.strip()[2:].strip().strip('"\''))
            continue
        # key: value
        m = re.match(r"^(\w[\w-]*):\s*(.*)$", line)
        if m:
            key, val = m.group(1), m.group(2).strip()
            current_key = key
            current_list = None
            if val:
                # 去掉引号
                val = val.strip('"\'')
                # 布尔值
                if val.lower() == "true":
                    val = True
                elif val.lower() == "false":
                    val = False
                fm[key] = val
            else:
                fm[key] = None  # 可能是列表
    return fm, end + 3


def update_front_matter(content, updates):
    """更新front matter中的字段，返回新内容"""
    fm, body_start = parse_front_matter(content)
    fm.update(updates)

    # 重新构建front matter
    lines = ["---"]
    for key, val in fm.items():
        if isinstance(val, list):
            lines.append(f"{key}:")
            for item in val:
                lines.append(f"  - {item}")
        elif isinstance(val, bool):
            lines.append(f"{key}: {'true' if val else 'false'}")
        elif val is None:
            lines.append(f"{key}:")
        else:
            # 值包含特殊字符时加引号
            if any(c in str(val) for c in [':', '#', '[', ']', '{', '}', ',', '&', '*', '?', '|', '<', '>', '=', '!', '%', '@', '`']):
                lines.append(f'{key}: "{val}"')
            else:
                lines.append(f"{key}: {val}")
    lines.append("---")
    lines.append("")  # 空行分隔

    body = content[body_start:].lstrip("\n")
    return "\n".join(lines) + "\n" + body


def fetch_cat_image(api_idx=0):
    """从猫图API获取一张猫图，返回PIL Image或None"""
    if api_idx >= len(CAT_APIS):
        return None

    api = CAT_APIS[api_idx]
    print(f"  尝试 {api['name']}...", end=" ", flush=True)

    try:
        if api["json"]:
            # JSON API：先获取图片URL再下载
            resp = requests.get(api["url"], headers=HEADERS, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            if not data or "url" not in data[0]:
                raise ValueError("无图片URL")
            img_url = data[0]["url"]
            resp = requests.get(img_url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
        else:
            # 直接返回图片
            url = api["url"].format(w=COVER_WIDTH, h=COVER_HEIGHT)
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.raise_for_status()

        # 保存到临时文件再打开（避免内存问题）
        tmp_path = OUTPUT_DIR / f"_tmp_{int(time.time())}_{random.randint(1000,9999)}.jpg"
        tmp_path.write_bytes(resp.content)
        img = Image.open(tmp_path).convert("RGB")
        tmp_path.unlink(missing_ok=True)
        print("OK")
        return img

    except Exception as e:
        print(f"失败 ({e})")
        return fetch_cat_image(api_idx + 1)


def process_cat_image(img, category=""):
    """将猫图处理成猫系毛绒绒封面风格"""
    # 1. 裁剪到目标比例（居中裁剪）
    src_w, src_h = img.size
    target_ratio = COVER_WIDTH / COVER_HEIGHT
    src_ratio = src_w / src_h

    if src_ratio > target_ratio:
        # 太宽，裁左右
        new_w = int(src_h * target_ratio)
        left = (src_w - new_w) // 2
        img = img.crop((left, 0, left + new_w, src_h))
    else:
        # 太高，裁上下
        new_h = int(src_w / target_ratio)
        top = (src_h - new_h) // 2
        img = img.crop((0, top, src_w, top + new_h))

    # 2. 缩放到目标尺寸
    img = img.resize((COVER_WIDTH, COVER_HEIGHT), Image.LANCZOS)

    # 3. 加深紫蓝色调（叠加半透明色层）
    overlay = Image.new("RGB", (COVER_WIDTH, COVER_HEIGHT), CAT_BG)
    img = Image.blend(img, overlay, 0.35)

    # 4. 增强对比度和饱和度，让猫更突出
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.15)
    enhancer = ImageEnhance.Color(img)
    img = enhancer.enhance(1.2)

    # 5. 轻微毛绒质感（高斯模糊+原图叠加）
    blurred = img.filter(ImageFilter.GaussianBlur(radius=1.2))
    img = Image.blend(img, blurred, 0.15)

    # 6. 橙色渐变边框
    draw = ImageDraw.Draw(img)
    border_w = 6
    # 外边框
    for i in range(border_w):
        alpha_color = tuple(
            int(CAT_ACCENT[j] + (CAT_ACCENT2[j] - CAT_ACCENT[j]) * (i / border_w))
            for j in range(3)
        )
        draw.rectangle(
            [i, i, COVER_WIDTH - 1 - i, COVER_HEIGHT - 1 - i],
            outline=alpha_color,
            width=1,
        )

    # 7. 四角圆角遮罩
    mask = Image.new("L", (COVER_WIDTH, COVER_HEIGHT), 0)
    mask_draw = ImageDraw.Draw(mask)
    radius = 24
    mask_draw.rounded_rectangle([0, 0, COVER_WIDTH - 1, COVER_HEIGHT - 1], radius=radius, fill=255)
    # 创建圆角背景
    bg = Image.new("RGB", (COVER_WIDTH, COVER_HEIGHT), CAT_BG)
    bg.paste(img, (0, 0), mask)
    img = bg

    # 8. 底部渐变暗化（放文字用）
    gradient = Image.new("L", (COVER_WIDTH, 120), 0)
    grad_draw = ImageDraw.Draw(gradient)
    for y in range(120):
        alpha = int(180 * (y / 120))
        grad_draw.line([(0, y), (COVER_WIDTH, y)], fill=alpha)
    dark_overlay = Image.new("RGB", (COVER_WIDTH, 120), (0, 0, 0))
    img.paste(dark_overlay, (0, COVER_HEIGHT - 120), gradient)

    # 9. 分类emoji水印（右下角）
    emoji = CATEGORY_EMOJI.get(category, "🐱")
    # 用文字绘制emoji（PIL对emoji支持有限，用简单圆形代替）
    # 这里画一个橙色圆形+白色猫爪印
    cx, cy = COVER_WIDTH - 60, COVER_HEIGHT - 55
    draw = ImageDraw.Draw(img)
    draw.ellipse([cx - 28, cy - 28, cx + 28, cy + 28], fill=CAT_ACCENT)
    # 猫爪印（简化：一个大圆+四个小圆）
    paw_color = CAT_BG
    draw.ellipse([cx - 10, cy - 4, cx + 10, cy + 14], fill=paw_color)
    for dx, dy in [(-16, -12), (-6, -18), (6, -18), (16, -12)]:
        draw.ellipse([cx + dx - 5, cy + dy - 5, cx + dx + 5, cy + dy + 5], fill=paw_color)

    return img


def get_article_category(fm):
    """从front matter获取分类名"""
    cats = fm.get("categories", [])
    if isinstance(cats, list) and cats:
        return cats[0]
    if isinstance(cats, str):
        return cats
    return ""


def generate_cover_name(md_path, fm):
    """生成封面文件名：分类-标题hash.jpg"""
    category = get_article_category(fm) or "misc"
    title = fm.get("title", md_path.stem)
    h = hashlib.md5(title.encode()).hexdigest()[:8]
    # 清理分类名中的特殊字符
    safe_cat = re.sub(r"[^\w\u4e00-\u9fff]", "", category)
    return f"{safe_cat}-{h}.jpg"


def main():
    force = "--force" in sys.argv
    dry_run = "--dry-run" in sys.argv

    print("=" * 60)
    print("🐱 喵喵小码 · 猫图封面自动生成器")
    print("=" * 60)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 扫描所有文章
    md_files = sorted(POSTS_DIR.glob("*.md"))
    print(f"\n📂 找到 {len(md_files)} 篇文章\n")

    results = {"success": [], "skip": [], "fail": []}

    for idx, md_path in enumerate(md_files, 1):
        content = md_path.read_text(encoding="utf-8")
        fm, _ = parse_front_matter(content)
        title = fm.get("title", md_path.stem)
        category = get_article_category(fm)

        # 检查是否已有cover
        existing_cover = fm.get("cover", "")
        cover_name = generate_cover_name(md_path, fm)
        cover_path = OUTPUT_DIR / cover_name

        if existing_cover and not force and cover_path.exists():
            print(f"[{idx}/{len(md_files)}] ⏭️  跳过（已有封面）: {title}")
            results["skip"].append(title)
            continue

        print(f"[{idx}/{len(md_files)}] 🐱 处理: {title} [{category}]")

        if dry_run:
            print(f"    [dry-run] 将保存为: {cover_name}")
            results["success"].append(title)
            continue

        # 获取猫图
        img = fetch_cat_image()
        if img is None:
            print(f"    ❌ 所有API都失败了，跳过")
            results["fail"].append(title)
            continue

        # 处理图片
        try:
            processed = process_cat_image(img, category)
            processed.save(cover_path, "JPEG", quality=85, optimize=True)
            print(f"    ✅ 保存: images/cat-covers/{cover_name}")
        except Exception as e:
            print(f"    ❌ 图片处理失败: {e}")
            results["fail"].append(title)
            continue

        # 更新文章front matter
        cover_url = f"/images/cat-covers/{cover_name}"
        new_content = update_front_matter(content, {"cover": cover_url})
        md_path.write_text(new_content, encoding="utf-8")
        print(f"    📝 更新cover: {cover_url}")

        results["success"].append(title)

        # 礼貌延迟，避免被API封
        time.sleep(random.uniform(0.8, 1.8))

    # 汇总
    print("\n" + "=" * 60)
    print("📊 完成汇总")
    print("=" * 60)
    print(f"  ✅ 成功: {len(results['success'])}")
    print(f"  ⏭️  跳过: {len(results['skip'])}")
    print(f"  ❌ 失败: {len(results['fail'])}")
    if results["fail"]:
        print(f"\n  失败列表:")
        for t in results["fail"]:
            print(f"    - {t}")
    print(f"\n  封面图目录: {OUTPUT_DIR}")
    print(f"  封面图数量: {len(list(OUTPUT_DIR.glob('*.jpg')))}")
    print("=" * 60)


if __name__ == "__main__":
    main()
