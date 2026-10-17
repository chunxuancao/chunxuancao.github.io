#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
喵喵小码 · 二次元猫娘封面生成器
从搜索到的猫娘图CDN下载，居中裁剪成800x500，叠加白色毛绒边框+粉橙渐变边框+猫爪印
"""

import os
import sys
import hashlib
import requests
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

# 配置
BLOG_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = BLOG_ROOT / "source" / "images" / "cat-covers"
POSTS_DIR = BLOG_ROOT / "source" / "_posts"
COVER_WIDTH = 800
COVER_HEIGHT = 500

# 猫系配色
CAT_BG = (255, 248, 240)       # 米白
CAT_BG2 = (253, 243, 231)      # 暖米白
CAT_PINK = (255, 182, 193)     # 粉色
CAT_ACCENT = (255, 157, 92)    # 橙色
CAT_DARK = (74, 55, 40)        # 深棕

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

# 40张二次元猫娘图（来自image_search）
NEKOMIMI_URLS = [
    "https://aka.doubaocdn.com/s/VTtnXZMf35",  # 银发猫娘 白色背景 横版
    "https://aka.doubaocdn.com/s/Vc1DvWE6Rq",  # Q版猫娘 白色背景
    "https://aka.doubaocdn.com/s/D9PPyaEkA3",  # Q版猫娘 方形
    "https://aka.doubaocdn.com/s/MUsgABVCQk",  # 金发猫娘 粉色背景
    "https://aka.doubaocdn.com/s/FrDCdazZAV",  # 白发猫娘头像
    "https://aka.doubaocdn.com/s/HY70VrX42I",  # 白发猫娘女仆
    "https://aka.doubaocdn.com/s/ivo2SqUInN",  # 粉发猫娘 白色背景
    "https://aka.doubaocdn.com/s/izdYXsGJhq",  # 白发猫娘 深色背景
    "https://aka.doubaocdn.com/s/4ckUTKY2HH",  # Q版猫娘 灰色背景
    "https://aka.doubaocdn.com/s/gPfqJnMHVP",  # 粉发猫娘 白色背景
    "https://aka.doubaocdn.com/s/AYNPRdOE1j",  # 白发猫娘 白色背景
    "https://aka.doubaocdn.com/s/VZndVwyR2h",  # 白发猫娘 深色背景
    "https://aka.doubaocdn.com/s/EYsvUFV14Y",  # 金发猫娘女仆
    "https://aka.doubaocdn.com/s/Nb2MOHrIKI",  # 40原猫娘 白色背景
    "https://aka.doubaocdn.com/s/53SO5v40tu",  # 粉发猫娘 深色背景
    "https://aka.doubaocdn.com/s/1mUUDyDB7W",  # Q版猫娘 白色背景
    "https://aka.doubaocdn.com/s/c6C6jK97M2",  # 白毛猫娘 深色背景
    "https://aka.doubaocdn.com/s/3cCSpyRXvP",  # Q版猫娘 白色背景
    "https://aka.doubaocdn.com/s/G9ctyTBKVJ",  # 猫娘 白色背景
    "https://aka.doubaocdn.com/s/JOVzJ9s6ld",  # 白发猫娘 蓝天背景
    "https://aka.doubaocdn.com/s/0B3llPZbmx",  # 黑猫耳少女
    "https://aka.doubaocdn.com/s/R79TxeiaHA",  # 白发猫耳少女 粉色衣服
    "https://aka.doubaocdn.com/s/l8598UlkIk",  # 白发猫耳少女头像
    "https://aka.doubaocdn.com/s/F4YPOJ7y9D",  # 棕发猫耳少女 时钟背景
    "https://aka.doubaocdn.com/s/Cc5lrrex5D",  # 金发猫耳睡衣少女
    "https://aka.doubaocdn.com/s/U2tuRz6lUK",  # 长发猫耳少女 雪景
    "https://aka.doubaocdn.com/s/8RVqFjPXOj",  # 白发猫耳少女 耳机
    "https://aka.doubaocdn.com/s/rWPuPtx3A4",  # 长发猫耳少女 雪景 横版
    "https://aka.doubaocdn.com/s/l5A6xlU3GJ",  # 黑发猫耳少女 围巾
    "https://aka.doubaocdn.com/s/54Yw8j8peU",  # 灰发猫耳少女 白色裙子
    "https://aka.doubaocdn.com/s/VDVVaa5Zza",  # 黑发猫耳少女 花
    "https://aka.doubaocdn.com/s/n0JfvQZUug",  # 黑发猫耳少女 背包
    "https://aka.doubaocdn.com/s/Nrz48TmAcG",  # 蓝发猫耳少女 城市
    "https://aka.doubaocdn.com/s/HqpuBmSWTV",  # 黑猫耳少女 红色背景
    "https://aka.doubaocdn.com/s/WefpZ5oveK",  # 黑发猫耳少女 水手服
    "https://aka.doubaocdn.com/s/THCSfxVYXD",  # 长发猫耳少女 雪景 横版
    "https://aka.doubaocdn.com/s/VzCtlM5aJS",  # 紫发猫耳少女 校服
    "https://aka.doubaocdn.com/s/ICrMjeKl12",  # 金发猫耳少女 窗帘
    "https://aka.doubaocdn.com/s/KriHA8Kjau",  # 黑发猫耳少女 玩游戏
    "https://aka.doubaocdn.com/s/vmLeJCQHTN",  # 蓝发猫耳少女 头像
]


def download_image(url, save_path):
    """下载图片"""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        save_path.write_bytes(resp.content)
        return True
    except Exception as e:
        print(f"    下载失败: {e}")
        return False


def crop_to_cover(img):
    """居中裁剪到800x500"""
    src_w, src_h = img.size
    target_ratio = COVER_WIDTH / COVER_HEIGHT
    src_ratio = src_w / src_h

    if src_ratio > target_ratio:
        # 原图太宽，裁剪左右
        new_w = int(src_h * target_ratio)
        left = (src_w - new_w) // 2
        img = img.crop((left, 0, left + new_w, src_h))
    else:
        # 原图太高，裁剪上下
        new_h = int(src_w / target_ratio)
        top = (src_h - new_h) // 2
        img = img.crop((0, top, src_w, top + new_h))

    return img.resize((COVER_WIDTH, COVER_HEIGHT), Image.LANCZOS)


def process_cover(neko_img):
    """将猫娘图处理成白色毛绒绒封面"""
    # 1. 裁剪到封面尺寸
    neko_img = crop_to_cover(neko_img)

    # 2. 创建米白渐变背景（作为边框底）
    bg = Image.new("RGB", (COVER_WIDTH, COVER_HEIGHT), CAT_BG)
    bg_draw = ImageDraw.Draw(bg)
    for y in range(COVER_HEIGHT):
        ratio = y / COVER_HEIGHT
        r = int(CAT_BG[0] + (CAT_BG2[0] - CAT_BG[0]) * ratio)
        g = int(CAT_BG[1] + (CAT_BG2[1] - CAT_BG[1]) * ratio)
        b = int(CAT_BG[2] + (CAT_BG2[2] - CAT_BG[2]) * ratio)
        bg_draw.line([(0, y), (COVER_WIDTH, y)], fill=(r, g, b))

    # 3. 毛绒噪点
    noise = Image.effect_noise((COVER_WIDTH, COVER_HEIGHT), 10).convert("L")
    noise_rgb = Image.merge("RGB", (noise, noise, noise))
    bg = Image.blend(bg, noise_rgb, 0.025)

    # 4. 猫娘图加白色毛绒边框
    border_pad = 10
    inner_w = COVER_WIDTH - border_pad * 2
    inner_h = COVER_HEIGHT - border_pad * 2
    neko_img = neko_img.resize((inner_w, inner_h), Image.LANCZOS)

    # 白色边框层
    border_layer = Image.new("RGB", (COVER_WIDTH, COVER_HEIGHT), (255, 255, 255))
    border_layer.paste(neko_img, (border_pad, border_pad))

    # 圆角遮罩
    mask = Image.new("L", (COVER_WIDTH, COVER_HEIGHT), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle([0, 0, COVER_WIDTH-1, COVER_HEIGHT-1], radius=20, fill=255)

    # 把带边框的猫娘图贴到背景上
    bg.paste(border_layer, (0, 0), mask)

    # 5. 粉橙渐变外边框
    border_w = 4
    for i in range(border_w):
        ratio = i / border_w
        r = int(CAT_PINK[0] + (CAT_ACCENT[0] - CAT_PINK[0]) * ratio)
        g = int(CAT_PINK[1] + (CAT_ACCENT[1] - CAT_PINK[1]) * ratio)
        b = int(CAT_PINK[2] + (CAT_ACCENT[2] - CAT_PINK[2]) * ratio)
        bg_draw = ImageDraw.Draw(bg)
        bg_draw.rectangle([i, i, COVER_WIDTH-1-i, COVER_HEIGHT-1-i], outline=(r, g, b), width=1)

    # 6. 整体圆角
    mask_final = Image.new("L", (COVER_WIDTH, COVER_HEIGHT), 0)
    mask_draw = ImageDraw.Draw(mask_final)
    mask_draw.rounded_rectangle([0, 0, COVER_WIDTH-1, COVER_HEIGHT-1], radius=24, fill=255)
    final = Image.new("RGB", (COVER_WIDTH, COVER_HEIGHT), CAT_BG)
    final.paste(bg, (0, 0), mask_final)
    bg = final

    # 7. 右下角猫爪印
    paw_draw = ImageDraw.Draw(bg)
    paw_cx, paw_cy = COVER_WIDTH - 45, COVER_HEIGHT - 40
    paw_draw.ellipse([paw_cx-16, paw_cy-16, paw_cx+16, paw_cy+16], fill=CAT_ACCENT)
    paw_draw.ellipse([paw_cx-10, paw_cy-7, paw_cx+10, paw_cy+11], fill=CAT_BG)
    for dx, dy in [(-12, -11), (-4, -16), (4, -16), (12, -11)]:
        paw_draw.ellipse([paw_cx+dx-4, paw_cy+dy-4, paw_cx+dx+4, paw_cy+dy+4], fill=CAT_BG)

    return bg


def parse_front_matter(content):
    """简单解析front matter"""
    if not content.startswith("---"):
        return {}, 0
    end = content.find("---", 3)
    if end == -1:
        return {}, 0
    fm_text = content[3:end].strip()
    fm = {}
    for line in fm_text.split("\n"):
        line = line.strip()
        if ":" in line and not line.startswith("-"):
            key, val = line.split(":", 1)
            fm[key.strip()] = val.strip().strip('"\'')
    return fm, end + 3


def update_cover_in_md(md_path, cover_url):
    """更新md文件的cover字段"""
    content = md_path.read_text(encoding="utf-8")
    fm, body_start = parse_front_matter(content)

    lines = ["---"]
    found_cover = False
    for line in content[3:body_start-3].split("\n"):
        if line.strip().startswith("cover:"):
            lines.append(f"cover: {cover_url}")
            found_cover = True
        else:
            lines.append(line)
    if not found_cover:
        lines.append(f"cover: {cover_url}")
    lines.append("---")
    lines.append("")

    body = content[body_start:].lstrip("\n")
    new_content = "\n".join(lines) + "\n" + body
    md_path.write_text(new_content, encoding="utf-8")


def main():
    force = "--force" in sys.argv
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("🐱 喵喵小码 · 二次元猫娘封面生成器")
    print("=" * 60)

    posts = sorted(POSTS_DIR.glob("*.md"))
    print(f"\n📂 找到 {len(posts)} 篇文章")
    print(f"🖼️  猫娘图库: {len(NEKOMIMI_URLS)} 张\n")

    success = 0
    fail = 0

    for idx, md_path in enumerate(posts, 1):
        fm, _ = parse_front_matter(md_path.read_text(encoding="utf-8"))
        title = fm.get("title", md_path.stem)

        # 根据标题hash选择猫娘图
        url_idx = int(hashlib.md5(title.encode()).hexdigest(), 16) % len(NEKOMIMI_URLS)
        neko_url = NEKOMIMI_URLS[url_idx]

        # 生成封面文件名
        h = hashlib.md5(title.encode()).hexdigest()[:8]
        cover_name = f"neko-{h}.jpg"
        cover_path = OUTPUT_DIR / cover_name

        print(f"[{idx}/{len(posts)}] 🎨 {title[:40]}")
        print(f"    猫娘图: #{url_idx+1}")

        if cover_path.exists() and not force:
            print(f"    ⏭️  已存在，跳过")
            success += 1
            continue

        # 下载猫娘图
        tmp_path = OUTPUT_DIR / f"_tmp_{h}.jpg"
        if not download_image(neko_url, tmp_path):
            fail += 1
            continue

        # 处理封面
        try:
            neko_img = Image.open(tmp_path).convert("RGB")
            cover = process_cover(neko_img)
            cover.save(cover_path, "JPEG", quality=90, optimize=True)
            tmp_path.unlink(missing_ok=True)
            print(f"    ✅ 保存: images/cat-covers/{cover_name}")
            success += 1
        except Exception as e:
            print(f"    ❌ 处理失败: {e}")
            tmp_path.unlink(missing_ok=True)
            fail += 1

    print(f"\n{'=' * 60}")
    print(f"📊 完成: ✅ {success}  ❌ {fail}")
    print(f"📂 封面目录: {OUTPUT_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
