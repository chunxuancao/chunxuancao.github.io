---
title: Python爬虫常用库大全与对比
date: 2026-10-17 17:10:00
category: 工具推荐
tags: [Python, 爬虫库, 工具推荐, 入门]
difficulty: 入门
summary: Python爬虫开发常用库汇总，请求库、解析库、自动化库、异步库对比，选择合适的工具提高效率
cover: /images/tools-cover.jpg
---

## 适用场景

开发爬虫时不知道该用什么库，或者想了解有哪些好用的工具可以提高效率。需要一份全面的爬虫库对比和推荐。

## 实现原理

Python爬虫生态非常丰富，从请求、解析、自动化到异步、分布式，每个环节都有多个库可选。不同的库有不同的特点和适用场景，选择合适的库可以大幅提高开发效率。

## 具体步骤

### 第一步：请求库

**1. requests（最常用）**
- 特点：简单易用，API友好，文档完善
- 适用：90%的普通爬虫
- 安装：`pip install requests`
- 示例：
```python
import requests
response = requests.get("https://example.com")
print(response.text)
```

**2. httpx（支持异步）**
- 特点：支持同步和异步，HTTP/2，比requests更现代
- 适用：需要异步请求的场景
- 安装：`pip install httpx`
- 示例：
```python
import httpx
response = httpx.get("https://example.com")
```

**3. aiohttp（异步）**
- 特点：纯异步，高并发性能好
- 适用：高并发爬虫
- 安装：`pip install aiohttp`
- 示例：
```python
import aiohttp
import asyncio

async def fetch():
    async with aiohttp.ClientSession() as session:
        async with session.get("https://example.com") as resp:
            return await resp.text()
```

**4. urllib（标准库）**
- 特点：Python内置，不需要安装
- 适用：简单请求，不想装依赖
- 缺点：API比较底层，用起来麻烦

**对比：**
| 库 | 异步 | 易用性 | 性能 | 推荐度 |
|----|------|--------|------|--------|
| requests | 否 | 高 | 中 | ⭐⭐⭐⭐⭐ |
| httpx | 是 | 高 | 高 | ⭐⭐⭐⭐ |
| aiohttp | 是 | 中 | 高 | ⭐⭐⭐⭐ |
| urllib | 否 | 低 | 中 | ⭐⭐ |

### 第二步：解析库

**1. BeautifulSoup4（最常用）**
- 特点：简单易学，API友好，适合新手
- 适用：HTML解析，简单爬虫
- 安装：`pip install beautifulsoup4 lxml`

**2. lxml + XPath（速度快）**
- 特点：C语言实现，速度快，XPath功能强大
- 适用：大量数据解析，性能要求高
- 安装：`pip install lxml`

**3. pyquery（jQuery风格）**
- 特点：jQuery风格的API，前端开发者友好
- 适用：熟悉jQuery的人
- 安装：`pip install pyquery`

**4. parsel（Scrapy御用）**
- 特点：Scrapy的解析库，支持XPath和CSS
- 适用：Scrapy项目
- 安装：`pip install parsel`

**对比：**
| 库 | 速度 | 易用性 | 功能 | 推荐度 |
|----|------|--------|------|--------|
| BeautifulSoup | 中 | 高 | 中 | ⭐⭐⭐⭐ |
| lxml/XPath | 高 | 中 | 高 | ⭐⭐⭐⭐⭐ |
| pyquery | 中 | 高 | 中 | ⭐⭐⭐ |
| parsel | 高 | 中 | 高 | ⭐⭐⭐⭐ |

### 第三步：自动化库

**1. Selenium（最经典）**
- 特点：生态成熟，文档多，支持多浏览器
- 适用：JS渲染页面，自动化操作
- 缺点：速度慢，资源占用高
- 安装：`pip install selenium`

**2. Playwright（推荐）**
- 特点：微软出品，速度快，自动等待，API现代
- 适用：现代爬虫，自动化测试
- 优点：比Selenium快，网络拦截功能强
- 安装：`pip install playwright && playwright install`

**3. Puppeteer（Node.js）**
- 特点：Google出品，Node.js生态
- 适用：Node.js开发者
- Python版：pyppeteer（不太维护了）

**对比：**
| 库 | 速度 | 易用性 | 功能 | 推荐度 |
|----|------|--------|------|--------|
| Selenium | 慢 | 高 | 高 | ⭐⭐⭐⭐ |
| Playwright | 快 | 高 | 很高 | ⭐⭐⭐⭐⭐ |
| Puppeteer | 快 | 高 | 高 | ⭐⭐⭐（Node.js） |

### 第四步：异步和并发

**1. asyncio + aiohttp**
- 特点：Python标准异步方案
- 适用：高并发爬虫
- 并发量：几百到几千

**2. Scrapy（框架）**
- 特点：异步框架，自带调度、去重、管道
- 适用：中大型爬虫项目
- 安装：`pip install scrapy`

**3. Celery（分布式任务）**
- 特点：分布式任务队列
- 适用：超大规模分布式爬虫
- 安装：`pip install celery`

### 第五步：反爬相关库

**1. fake-useragent（随机UA）**
- 功能：生成随机User-Agent
- 安装：`pip install fake-useragent`

**2. ddddocr（验证码识别）**
- 功能：验证码OCR识别，识别率高
- 安装：`pip install ddddocr`

**3. PyExecJS（运行JS）**
- 功能：在Python中运行JS代码
- 安装：`pip install PyExecJS`

**4. pycryptodome（加密）**
- 功能：AES、RSA等加密算法
- 安装：`pip install pycryptodome`

**5. fonttools（字体反爬）**
- 功能：分析字体文件，破解字体反爬
- 安装：`pip install fonttools`

### 第六步：数据存储库

**1. csv（标准库）**
- 适用：小数据量，简单存储
- 优点：不需要额外依赖

**2. openpyxl（Excel）**
- 功能：读写Excel文件
- 安装：`pip install openpyxl`

**3. pymysql（MySQL）**
- 功能：连接MySQL数据库
- 安装：`pip install pymysql`

**4. pymongo（MongoDB）**
- 功能：连接MongoDB数据库
- 安装：`pip install pymongo`

**5. redis（缓存/去重）**
- 功能：Redis缓存，用于URL去重、队列
- 安装：`pip install redis`

### 第七步：工具库

**1. tqdm（进度条）**
- 功能：显示进度条
- 安装：`pip install tqdm`

**2. loguru（日志）**
- 功能：更友好的日志库
- 安装：`pip install loguru`

**3. tenacity（重试）**
- 功能：优雅的重试机制
- 安装：`pip install tenacity`

**4. pydantic（数据验证）**
- 功能：数据模型验证和序列化
- 安装：`pip install pydantic`

## 完整代码

```python
# requirements.txt - 爬虫常用库
# 基础请求
requests==2.31.0
httpx==0.25.0

# 解析
beautifulsoup4==4.12.0
lxml==4.9.0
pyquery==2.0.0

# 自动化
selenium==4.15.0
playwright==1.40.0

# 异步
aiohttp==3.9.0

# 框架
Scrapy==2.11.0

# 反爬
fake-useragent==1.4.0
ddddocr==1.4.0
PyExecJS==1.5.1
pycryptodome==3.19.0
fonttools==4.44.0

# 存储
openpyxl==3.1.2
pymysql==1.1.0
pymongo==4.6.0
redis==5.0.0

# 工具
tqdm==4.66.0
loguru==0.7.2
tenacity==8.2.3
pydantic==2.5.0
```

```python
# 爬虫项目模板 - 常用库组合
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_fixed
import csv

class BaseSpider:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        })
    
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    def fetch(self, url):
        logger.info(f"请求: {url}")
        response = self.session.get(url, timeout=10)
        response.raise_for_status()
        return response.text
    
    def parse(self, html):
        soup = BeautifulSoup(html, "lxml")
        items = []
        for item in soup.select(".item"):
            items.append({
                "title": item.select_one(".title").text,
                "url": item.select_one("a")["href"]
            })
        return items
    
    def save(self, items, filename="data.csv"):
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["title", "url"])
            writer.writeheader()
            writer.writerows(items)
        logger.info(f"保存{len(items)}条数据")
    
    def run(self, urls):
        all_items = []
        for url in tqdm(urls):
            html = self.fetch(url)
            items = self.parse(html)
            all_items.extend(items)
        self.save(all_items)
```

## 注意事项

1. **不要重复造轮子** — 有现成的库就用，不要自己写
2. **版本兼容** — 注意库的版本，有些库新版本API会变
3. **依赖管理** — 用requirements.txt或pyproject.toml管理依赖
4. **性能考虑** — 大量数据用lxml不用BeautifulSoup，高并发用异步
5. **安全考虑** — 不要用太冷门的库，可能有安全漏洞

## 进阶拓展

- 学习Scrapy框架，中大型项目首选
- 了解异步编程，提高爬虫效率
- 学习分布式爬虫（Scrapy-Redis）
- 了解爬虫监控和部署工具
