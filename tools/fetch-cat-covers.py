#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
喵喵小码 · 动漫风猫系封面自动生成器
====================================
功能：
  1. 扫描 source/_posts/ 下所有文章
  2. 从 DiceBear API 获取动漫风格头像（adventurer/lorelei 等）
  3. 用PIL统一处理成白色毛绒绒猫系风格（米白背景 + 粉橙边框 + 猫耳 + 圆角）
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

# 白色毛绒绒主题色
CAT_BG = (255, 248, 240)       # 米白背景
CAT_BG2 = (253, 243, 231)      # 浅米黄
CAT_ACCENT = (255, 157, 92)    # 橙色强调
CAT_ACCENT2 = (255, 185, 128)  # 浅橙
CAT_PINK = (255, 196, 214)     # 粉色
CAT_PINK2 = (255, 168, 192)    # 深粉
CAT_FUR = (232, 133, 74)       # 毛橙
CAT_TEXT = (74, 55, 40)        # 深棕文字

# 图片尺寸
COVER_WIDTH = 800
COVER_HEIGHT = 500
AVATAR_SIZE = 320  # 动漫头像大小

# 猫图API（真实猫图，后续用PIL动漫化处理）
CAT_APIS = [
    {"name": "cataas", "url": "https://cataas.com/cat?width={w}&height={h}", "json": False},
    {"name": "thecatapi", "url": "https://api.thecatapi.com/v1/images/search?limit=1", "json": True},
    {"name": "placekitten", "url": "https://placekitten.com/{w}/{h}", "json": False},
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "image/*,*/*;q=0.8",
}


# ── 工具函数 ──────────────────────────────────────────
def parse_front_matter(content):
    """解析Hexo front matter"""
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
        if line.strip().startswith("- ") and current_key:
            if current_list is None:
                current_list = []
                fm[current_key] = current_list
            current_list.append(line.strip()[2:].strip().strip('"\''))
            continue
        m = re.match(r"^(\w[\w-]*):\s*(.*)$", line)
        if m:
            key, val = m.group(1), m.group(2).strip()
            current_key = key
            current_list = None
            if val:
                val = val.strip('"\'')
                if val.lower() == "true":
                    val = True
                elif val.lower() == "false":
                    val = False
                fm[key] = val
            else:
                fm[key] = None
    return fm, end + 3


def update_front_matter(content, updates):
    """更新front matter"""
    fm, body_start = parse_front_matter(content)
    fm.update(updates)
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
            if any(c in str(val) for c in [':', '#', '[', ']', '{', '}', ',', '&', '*', '?', '|', '<', '>', '=', '!', '%', '@', '`']):
                lines.append(f'{key}: "{val}"')
            else:
                lines.append(f"{key}: {val}")
    lines.append("---")
    lines.append("")
    body = content[body_start:].lstrip("\n")
    return "\n".join(lines) + "\n" + body


def fetch_cat_image(api_idx=0):
    """从猫图API获取真实猫图，返回PIL Image"""
    if api_idx >= len(CAT_APIS):
        return None

    api = CAT_APIS[api_idx]
    print(f"  尝试 {api['name']}...", end=" ", flush=True)

    try:
        if api["json"]:
            resp = requests.get(api["url"], headers=HEADERS, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            if not data or "url" not in data[0]:
                raise ValueError("无图片URL")
            img_url = data[0]["url"]
            resp = requests.get(img_url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
        else:
            url = api["url"].format(w=COVER_WIDTH, h=COVER_HEIGHT)
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.raise_for_status()

        tmp_path = OUTPUT_DIR / f"_tmp_{int(time.time())}_{random.randint(1000,9999)}.jpg"
        tmp_path.write_bytes(resp.content)
        img = Image.open(tmp_path).convert("RGB")
        tmp_path.unlink(missing_ok=True)
        print("OK")
        return img

    except Exception as e:
        print(f"失败 ({e})")
        return fetch_cat_image(api_idx + 1)


def draw_cat_ears(draw, cx, cy, size, color):
    """在头像上方画一对猫耳"""
    ear_w = size * 0.35
    ear_h = size * 0.45
    # 左耳
    left_ear = [
        (cx - size * 0.35, cy - size * 0.1),
        (cx - size * 0.15, cy - size * 0.55),
        (cx - size * 0.02, cy - size * 0.15),
    ]
    # 右耳
    right_ear = [
        (cx + size * 0.35, cy - size * 0.1),
        (cx + size * 0.15, cy - size * 0.55),
        (cx + size * 0.02, cy - size * 0.15),
    ]
    draw.polygon(left_ear, fill=color)
    draw.polygon(right_ear, fill=color)
    # 内耳（粉色）
    inner_color = CAT_PINK
    inner_left = [
        (cx - size * 0.28, cy - size * 0.12),
        (cx - size * 0.17, cy - size * 0.42),
        (cx - size * 0.08, cy - size * 0.15),
    ]
    inner_right = [
        (cx + size * 0.28, cy - size * 0.12),
        (cx + size * 0.17, cy - size * 0.42),
        (cx + size * 0.08, cy - size * 0.15),
    ]
    draw.polygon(inner_left, fill=inner_color)
    draw.polygon(inner_right, fill=inner_color)


def animefy_cat(img):
    """将真实猫图动漫化处理：颜色量化 + 边缘增强 + 平滑"""
    # 1. 中值滤波去噪
    img = img.filter(ImageFilter.MedianFilter(size=3))
    # 2. 颜色量化到24色（动漫色块效果）
    img = img.quantize(colors=24, method=Image.Quantize.MEDIANCUT).convert("RGB")
    # 3. 边缘增强
    img = img.filter(ImageFilter.EDGE_ENHANCE_MORE)
    # 4. 轻微平滑，让色块更柔和
    img = img.filter(ImageFilter.SMOOTH)
    # 5. 提升饱和度，让颜色更鲜艳
    enhancer = ImageEnhance.Color(img)
    img = enhancer.enhance(1.3)
    # 6. 提升对比度
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.1)
    return img


def process_anime_cover(cat_img, category=""):
    """将真实猫图动漫化后，处理成白色毛绒绒封面"""
    # 1. 创建米白渐变背景
    bg = Image.new("RGB", (COVER_WIDTH, COVER_HEIGHT), CAT_BG)
    bg_draw = ImageDraw.Draw(bg)
    for y in range(COVER_HEIGHT):
        ratio = y / COVER_HEIGHT
        r = int(CAT_BG[0] + (CAT_BG2[0] - CAT_BG[0]) * ratio)
        g = int(CAT_BG[1] + (CAT_BG2[1] - CAT_BG[1]) * ratio)
        b = int(CAT_BG[2] + (CAT_BG2[2] - CAT_BG[2]) * ratio)
        bg_draw.line([(0, y), (COVER_WIDTH, y)], fill=(r, g, b))

    # 2. 添加毛绒噪点纹理
    noise = Image.effect_noise((COVER_WIDTH, COVER_HEIGHT), 12).convert("L")
    noise_rgb = Image.merge("RGB", (noise, noise, noise))
    bg = Image.blend(bg, noise_rgb, 0.03)

    # 3. 背景装饰：漂浮的猫爪印
    deco_draw = ImageDraw.Draw(bg)
    random.seed(hash(category) % 10000)
    for _ in range(10):
        px = random.randint(30, COVER_WIDTH - 30)
        py = random.randint(30, COVER_HEIGHT - 30)
        s = random.randint(6, 16)
        deco_draw.ellipse([px - s//2, py - s//2, px + s//2, py + s//2], fill=CAT_PINK)
        for dx, dy in [(-s, -s//2), (-s//3, -s), (s//3, -s), (s, -s//2)]:
            deco_draw.ellipse([px+dx-s//4, py+dy-s//4, px+dx+s//4, py+dy+s//4], fill=CAT_PINK)
    random.seed()

    # 4. 动漫化猫图
    # 裁剪到4:3比例（居中）
    src_w, src_h = cat_img.size
    target_ratio = 4 / 3
    src_ratio = src_w / src_h
    if src_ratio > target_ratio:
        new_w = int(src_h * target_ratio)
        left = (src_w - new_w) // 2
        cat_img = cat_img.crop((left, 0, left + new_w, src_h))
    else:
        new_h = int(src_w / target_ratio)
        top = (src_h - new_h) // 2
        cat_img = cat_img.crop((0, top, src_w, top + new_h))

    # 缩放到合适大小（占封面75%宽度）
    cat_w = int(COVER_WIDTH * 0.72)
    cat_h = int(cat_w * 3 / 4)
    cat_img = cat_img.resize((cat_w, cat_h), Image.LANCZOS)

    # 动漫化
    cat_img = animefy_cat(cat_img)

    # 5. 猫图白色毛绒边框
    border_pad = 12
    framed_w = cat_w + border_pad * 2
    framed_h = cat_h + border_pad * 2
    framed = Image.new("RGB", (framed_w, framed_h), (255, 255, 255))
    framed.paste(cat_img, (border_pad, border_pad))
    # 圆角
    mask_round = Image.new("L", (framed_w, framed_h), 0)
    mask_draw = ImageDraw.Draw(mask_round)
    mask_draw.rounded_rectangle([0, 0, framed_w-1, framed_h-1], radius=18, fill=255)
    framed_bg = Image.new("RGB", (framed_w, framed_h), CAT_BG)
    framed_bg.paste(framed, (0, 0), mask_round)
    framed = framed_bg

    # 6. 粘贴到封面中央
    cx = COVER_WIDTH // 2
    cy = COVER_HEIGHT // 2
    bg.paste(framed, (cx - framed_w // 2, cy - framed_h // 2))

    # 7. 粉橙渐变外边框
    border_w = 5
    for i in range(border_w):
        ratio = i / border_w
        r = int(CAT_PINK[0] + (CAT_ACCENT[0] - CAT_PINK[0]) * ratio)
        g = int(CAT_PINK[1] + (CAT_ACCENT[1] - CAT_PINK[1]) * ratio)
        b = int(CAT_PINK[2] + (CAT_ACCENT[2] - CAT_PINK[2]) * ratio)
        bg_draw = ImageDraw.Draw(bg)
        bg_draw.rectangle([i, i, COVER_WIDTH-1-i, COVER_HEIGHT-1-i], outline=(r,g,b), width=1)

    # 8. 整体圆角
    mask_final = Image.new("L", (COVER_WIDTH, COVER_HEIGHT), 0)
    mask_draw = ImageDraw.Draw(mask_final)
    mask_draw.rounded_rectangle([0, 0, COVER_WIDTH-1, COVER_HEIGHT-1], radius=24, fill=255)
    final = Image.new("RGB", (COVER_WIDTH, COVER_HEIGHT), CAT_BG)
    final.paste(bg, (0, 0), mask_final)
    bg = final

    # 9. 右下角猫爪印
    paw_draw = ImageDraw.Draw(bg)
    paw_cx, paw_cy = COVER_WIDTH - 50, COVER_HEIGHT - 45
    paw_draw.ellipse([paw_cx-18, paw_cy-18, paw_cx+18, paw_cy+18], fill=CAT_ACCENT)
    paw_draw.ellipse([paw_cx-11, paw_cy-8, paw_cx+11, paw_cy+12], fill=CAT_BG)
    for dx, dy in [(-14, -13), (-5, -18), (5, -18), (14, -13)]:
        paw_draw.ellipse([paw_cx+dx-5, paw_cy+dy-5, paw_cx+dx+5, paw_cy+dy+5], fill=CAT_BG)

    return bg


def get_article_category(fm):
    cats = fm.get("categories", [])
    if isinstance(cats, list) and cats:
        return cats[0]
    if isinstance(cats, str):
        return cats
    return ""


def generate_cover_name(md_path, fm):
    category = get_article_category(fm) or "misc"
    title = fm.get("title", md_path.stem)
    h = hashlib.md5(title.encode()).hexdigest()[:8]
    safe_cat = re.sub(r"[^\w\u4e00-\u9fff]", "", category)
    return f"cat-{safe_cat}-{h}.jpg"


def main():
    force = "--force" in sys.argv
    dry_run = "--dry-run" in sys.argv

    print("=" * 60)
    print("🐱 喵喵小码 · 动漫风猫系封面生成器")
    print("=" * 60)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    md_files = sorted(POSTS_DIR.glob("*.md"))
    print(f"\n📂 找到 {len(md_files)} 篇文章\n")

    results = {"success": [], "skip": [], "fail": []}

    for idx, md_path in enumerate(md_files, 1):
        content = md_path.read_text(encoding="utf-8")
        fm, _ = parse_front_matter(content)
        title = fm.get("title", md_path.stem)
        category = get_article_category(fm)

        cover_name = generate_cover_name(md_path, fm)
        cover_path = OUTPUT_DIR / cover_name

        existing_cover = fm.get("cover", "")
        if existing_cover and not force and cover_path.exists():
            print(f"[{idx}/{len(md_files)}] ⏭️  跳过: {title}")
            results["skip"].append(title)
            continue

        print(f"[{idx}/{len(md_files)}] 🎨 生成: {title} [{category}]")

        if dry_run:
            print(f"    [dry-run] 将保存为: {cover_name}")
            results["success"].append(title)
            continue

        # 获取真实猫图
        cat_img = fetch_cat_image()
        if cat_img is None:
            print(f"    ❌ 获取猫图失败，跳过")
            results["fail"].append(title)
            continue

        # 处理封面（动漫化）
        try:
            cover = process_anime_cover(cat_img, category)
            cover.save(cover_path, "JPEG", quality=88, optimize=True)
            print(f"    ✅ 保存: images/cat-covers/{cover_name}")
        except Exception as e:
            print(f"    ❌ 处理失败: {e}")
            results["fail"].append(title)
            continue

        # 更新文章
        cover_url = f"/images/cat-covers/{cover_name}"
        new_content = update_front_matter(content, {"cover": cover_url})
        md_path.write_text(new_content, encoding="utf-8")
        print(f"    📝 更新cover: {cover_url}")

        results["success"].append(title)
        time.sleep(random.uniform(0.3, 0.8))

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
    print(f"  封面图数量: {len(list(OUTPUT_DIR.glob('anime-*.jpg')))}")
    print("=" * 60)


if __name__ == "__main__":
    main()
