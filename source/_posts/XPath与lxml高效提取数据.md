---
title: XPath与lxml高效提取数据
date: "2026-10-17 09:40:00"
category: 环境配置
tags: "[XPath, lxml, 网页解析, 基础]"
difficulty: 简单
summary: XPath语法与lxml库使用教程，比BeautifulSoup更快的解析方式，爬虫数据提取进阶必备
cover: https://aka.doubaocdn.com/s/4LYSbwyuTb
---

## 适用场景

BeautifulSoup速度不够快，或者需要更精确地定位元素。XPath是爬虫工程师最常用的解析方式，速度快、表达能力强。

## 实现原理

XPath是一种在XML/HTML文档中查找信息的语言，通过路径表达式来选取节点。lxml是Python的XML/HTML解析库，用C语言实现，速度非常快，支持XPath语法。

## 具体步骤

### 第一步：安装

```bash
pip install lxml
```

### 第二步：基础用法

```python
from lxml import etree

html = """
<html>
<body>
<div class="content">
  <h1>标题</h1>
  <p class="text">第一段</p>
  <p class="text">第二段</p>
  <a href="https://example.com" id="link1">链接</a>
  <ul>
    <li>项目1</li>
    <li>项目2</li>
  </ul>
</div>
</body>
</html>
"""

# 解析HTML
tree = etree.HTML(html)
```

### 第三步：XPath基础语法

```python
# 标签选择
tree.xpath("//h1")  # 所有h1标签
tree.xpath("/html/body/div")  # 绝对路径

# 属性选择
tree.xpath('//a[@id="link1"]')  # id为link1的a标签
tree.xpath('//p[@class="text"]')  # class为text的p标签
tree.xpath('//a[@href]')  # 有href属性的a标签

# 文本提取
tree.xpath("//h1/text()")  # h1的文本
tree.xpath("//a/text()")   # a标签的文本

# 属性提取
tree.xpath('//a/@href')  # a标签的href属性
tree.xpath('//a/@id')    # a标签的id属性
```

### 第四步：高级语法

```python
# 多条件
tree.xpath('//div[@class="content" and @id="main"]')

# 模糊匹配
tree.xpath('//div[contains(@class, "content")]')
tree.xpath('//a[starts-with(@href, "https")]')

# 位置选择
tree.xpath("//li[1]")       # 第一个li
tree.xpath("//li[last()]")  # 最后一个li
tree.xpath("//li[position()<3]")  # 前两个

# 层级关系
tree.xpath("//div/p")       # div下的所有p
tree.xpath("//div/p[1]")    # div下的第一个p
tree.xpath("//div//a")      # div下的所有后代a

# 逻辑运算
tree.xpath("//a | //p")     # 所有a和p
tree.xpath("//div[not(@class)]")  # 没有class的div
```

### 第五步：提取列表数据

```python
# 提取文章列表
articles = tree.xpath('//div[@class="article-list"]/div')
for article in articles:
    title = article.xpath('.//h2/text()')[0] if article.xpath('.//h2/text()') else ''
    url = article.xpath('.//a/@href')[0] if article.xpath('.//a/@href') else ''
    date = article.xpath('.//span[@class="date"]/text()')[0] if article.xpath('.//span[@class="date"]/text()') else ''
    print(f"{title} - {url} - {date}")
```

## 完整代码

```python
import requests
from lxml import etree

class XPathSpider:
    def __init__(self):
        self.headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    def fetch(self, url):
        response = requests.get(url, headers=self.headers, timeout=10)
        response.encoding = 'utf-8'
        return response.text
    
    def parse(self, html):
        tree = etree.HTML(html)
        
        # 文章列表
        items = []
        articles = tree.xpath('//div[@class="post-item"]')
        for article in articles:
            item = {
                "title": self.extract_text(article, './/h2/a/text()'),
                "url": self.extract_text(article, './/h2/a/@href'),
                "summary": self.extract_text(article, './/p[@class="summary"]/text()'),
                "date": self.extract_text(article, './/time/text()'),
                "tags": article.xpath('.//span[@class="tag"]/text()')
            }
            items.append(item)
        return items
    
    def extract_text(self, element, xpath_expr):
        """安全提取文本，避免索引错误"""
        result = element.xpath(xpath_expr)
        return result[0].strip() if result else ""

if __name__ == "__main__":
    spider = XPathSpider()
    html = spider.fetch("https://example.com")
    data = spider.parse(html)
    for item in data:
        print(item)
```

## 注意事项

1. **索引从1开始** — XPath的索引是从1开始的，不是0，这是最常见的错误
2. **相对路径** — 在循环里用.//开头表示相对当前节点，不要用//，否则会从根节点找
3. **空值处理** — xpath返回列表，找不到是空列表，直接[0]会报错，要先判断
4. **class精确匹配** — @class="text"是精确匹配，多class时用contains
5. **命名空间** — 有些XML有命名空间，需要处理，HTML一般没有

## 进阶拓展

- 学习XPath轴（axis）：ancestor、following、preceding等
- 了解CSS选择器和XPath的转换关系
- 学习lxml的ElementTree API
- 了解XPath 2.0的新特性
