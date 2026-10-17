---
title: BeautifulSoup4网页解析完全指南
date: "2026-10-17 09:30:00"
category: 环境配置
tags: "[BeautifulSoup, 网页解析, 基础, 新手入门]"
difficulty: 入门
summary: BeautifulSoup4解析HTML完全教程，标签查找、属性提取、CSS选择器、遍历文档树，爬虫数据提取必备
cover: https://aka.doubaocdn.com/s/ERoiQvJaT8
---

## 适用场景

已经能用requests拿到HTML，但不知道怎么从中提取需要的数据。BeautifulSoup是最常用的HTML解析库，简单易学。

## 实现原理

BeautifulSoup把复杂的HTML文档转换成一个复杂的树形结构，每个节点都是Python对象，可以通过标签名、属性、CSS选择器来查找和提取数据。

## 具体步骤

### 第一步：安装

```bash
pip install beautifulsoup4 lxml
```

lxml是解析器，速度比默认的html.parser快。

### 第二步：基础用法

```python
from bs4 import BeautifulSoup

html = """
<html>
<head><title>测试页面</title></head>
<body>
<div class="content">
  <h1>标题</h1>
  <p class="text">第一段文字</p>
  <p class="text">第二段文字</p>
  <a href="https://example.com" id="link1">链接</a>
  <ul>
    <li>项目1</li>
    <li>项目2</li>
  </ul>
</div>
</body>
</html>
"""

soup = BeautifulSoup(html, "lxml")
```

### 第三步：查找元素

```python
# find：找第一个匹配的元素
title = soup.find("title")
print(title.text)  # 测试页面

# find_all：找所有匹配的元素
p_list = soup.find_all("p")
for p in p_list:
    print(p.text)

# 按class查找
soup.find_all("p", class_="text")

# 按id查找
soup.find("a", id="link1")

# 按属性查找
soup.find("a", href="https://example.com")

# 多条件查找
soup.find_all("p", {"class": "text", "data-id": "123"})
```

### 第四步：CSS选择器（推荐）

```python
# 标签选择器
soup.select("title")

# class选择器
soup.select(".text")

# id选择器
soup.select("#link1")

# 后代选择器
soup.select(".content p")

# 子元素选择器
soup.select(".content > p")

# 属性选择器
soup.select('a[href="https://example.com"]')

# 选择第一个
soup.select_one(".text")
```

### 第五步：提取数据

```python
tag = soup.find("a", id="link1")

# 获取文本
print(tag.text)          # 链接
print(tag.get_text())    # 同上
print(tag.string)        # 直接子文本

# 获取属性
print(tag["href"])           # https://example.com
print(tag.get("href"))       # 同上
print(tag.attrs)             # 所有属性字典

# 获取标签名
print(tag.name)  # a
```

### 第六步：遍历文档树

```python
content = soup.find("div", class_="content")

# 子节点
print(content.contents)   # 直接子节点列表
print(content.children)   # 子节点迭代器

# 所有后代节点
for desc in content.descendants:
    print(desc)

# 父节点
print(content.parent)

# 兄弟节点
print(content.find_next_sibling())
print(content.find_previous_sibling())
```

## 完整代码

```python
import requests
from bs4 import BeautifulSoup

def parse_article(html):
    """解析文章页面"""
    soup = BeautifulSoup(html, "lxml")
    
    # 标题
    title = soup.select_one("h1.article-title").text.strip()
    
    # 作者
    author = soup.select_one(".author").text.strip()
    
    # 正文
    content = soup.select_one(".article-content").text.strip()
    
    # 图片列表
    images = [img["src"] for img in soup.select(".article-content img")]
    
    # 标签
    tags = [tag.text.strip() for tag in soup.select(".tag-list a")]
    
    return {
        "title": title,
        "author": author,
        "content": content,
        "images": images,
        "tags": tags
    }

if __name__ == "__main__":
    url = "https://example.com/article/123"
    response = requests.get(url)
    result = parse_article(response.text)
    print(result)
```

## 注意事项

1. **解析器选择** — 用lxml速度快，需要单独安装；html.parser是内置的但慢
2. **class_下划线** — BeautifulSoup里class是关键字，要用class_
3. **text vs string** — text会获取所有子孙文本，string只获取直接子文本
4. **编码问题** — 中文乱码时先设置response.encoding = 'utf-8'
5. **空值处理** — find找不到返回None，调用.text会报错，记得判空

## 进阶拓展

- 学习XPath和lxml，解析速度更快
- 了解pyquery，jQuery风格的解析库
- 学习正则表达式，处理复杂文本提取
- 了解BeautifulSoup的修改文档树功能
