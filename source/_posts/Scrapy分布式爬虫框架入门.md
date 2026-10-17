---
title: Scrapy分布式爬虫框架入门
date: 2026-10-17 17:40:00
category: 工具推荐
tags: [Scrapy, 框架, 分布式, 中等]
difficulty: 中等
summary: Scrapy爬虫框架入门教程，项目结构、Spider编写、中间件、管道、分布式部署，中大型爬虫首选
cover: /images/tools-cover.jpg
---

## 适用场景

爬虫项目越来越大，单文件写不过来，需要用框架管理。需要学习Scrapy框架，提高开发效率，支持分布式部署。

## 实现原理

Scrapy是一个为了爬取网站数据、提取结构性数据而编写的应用框架。它使用Twisted异步网络框架，自带调度器、下载器、解析器、管道等组件，开发者只需要编写Spider和Item，框架处理其他事情。

## 具体步骤

### 第一步：安装和创建项目

**安装：**
```bash
pip install scrapy
```

**创建项目：**
```bash
scrapy startproject myspider
cd myspider
```

**项目结构：**
```
myspider/
├── scrapy.cfg          # 配置文件
├── myspider/
│   ├── __init__.py
│   ├── items.py        # 数据模型定义
│   ├── middlewares.py  # 中间件
│   ├── pipelines.py    # 数据管道（存储）
│   ├── settings.py     # 配置文件
│   └── spiders/        # 爬虫目录
│       └── __init__.py
```

### 第二步：定义Item

```python
# items.py
import scrapy

class ProductItem(scrapy.Item):
    title = scrapy.Field()       # 商品标题
    price = scrapy.Field()       # 价格
    url = scrapy.Field()         # 商品链接
    image = scrapy.Field()       # 图片
    category = scrapy.Field()    # 分类
    crawl_time = scrapy.Field()  # 采集时间
```

### 第三步：编写Spider

```python
# spiders/product_spider.py
import scrapy
from myspider.items import ProductItem

class ProductSpider(scrapy.Spider):
    name = "product"  # 爬虫名称，运行时用
    allowed_domains = ["example.com"]  # 允许的域名
    start_urls = ["https://example.com/products"]  # 起始URL
    
    def parse(self, response):
        """解析列表页"""
        # 提取商品列表
        products = response.css(".product-item")
        for product in products:
            item = ProductItem()
            item['title'] = product.css(".title::text").get()
            item['price'] = product.css(".price::text").get()
            item['url'] = product.css("a::attr(href)").get()
            item['image'] = product.css("img::attr(src)").get()
            
            # 进入详情页
            detail_url = product.css("a::attr(href)").get()
            yield response.follow(detail_url, self.parse_detail, meta={'item': item})
        
        # 下一页
        next_page = response.css(".next::attr(href)").get()
        if next_page:
            yield response.follow(next_page, self.parse)
    
    def parse_detail(self, response):
        """解析详情页"""
        item = response.meta['item']
        item['category'] = response.css(".category::text").get()
        yield item
```

### 第四步：编写Pipeline（数据存储）

```python
# pipelines.py
import csv
import pymysql
from itemadapter import ItemAdapter

class CsvPipeline:
    """保存到CSV"""
    def open_spider(self, spider):
        self.file = open('products.csv', 'w', newline='', encoding='utf-8')
        self.writer = csv.DictWriter(self.file, fieldnames=['title', 'price', 'url', 'image', 'category', 'crawl_time'])
        self.writer.writeheader()
    
    def process_item(self, item, spider):
        self.writer.writerow(dict(item))
        return item
    
    def close_spider(self, spider):
        self.file.close()

class MysqlPipeline:
    """保存到MySQL"""
    def __init__(self, mysql_host, mysql_user, mysql_password, mysql_db):
        self.mysql_host = mysql_host
        self.mysql_user = mysql_user
        self.mysql_password = mysql_password
        self.mysql_db = mysql_db
    
    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mysql_host=crawler.settings.get('MYSQL_HOST'),
            mysql_user=crawler.settings.get('MYSQL_USER'),
            mysql_password=crawler.settings.get('MYSQL_PASSWORD'),
            mysql_db=crawler.settings.get('MYSQL_DB')
        )
    
    def open_spider(self, spider):
        self.conn = pymysql.connect(
            host=self.mysql_host,
            user=self.mysql_user,
            password=self.mysql_password,
            db=self.mysql_db,
            charset='utf8mb4'
        )
        self.cursor = self.conn.cursor()
    
    def process_item(self, item, spider):
        sql = "INSERT INTO products (title, price, url) VALUES (%s, %s, %s)"
        self.cursor.execute(sql, (item['title'], item['price'], item['url']))
        self.conn.commit()
        return item
    
    def close_spider(self, spider):
        self.cursor.close()
        self.conn.close()
```

### 第五步：编写中间件

```python
# middlewares.py
import random
from scrapy import signals

class UserAgentMiddleware:
    """随机User-Agent中间件"""
    def __init__(self):
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
        ]
    
    def process_request(self, request, spider):
        request.headers['User-Agent'] = random.choice(self.user_agents)

class ProxyMiddleware:
    """代理中间件"""
    def process_request(self, request, spider):
        request.meta['proxy'] = "http://your-proxy:port"
    
    def process_exception(self, request, exception, spider):
        # 代理失效，重新请求
        return request
```

### 第六步：配置settings.py

```python
# settings.py
BOT_NAME = 'myspider'
SPIDER_MODULES = ['myspider.spiders']
NEWSPIDER_MODULE = 'myspider.spiders'

# 遵守robots.txt
ROBOTSTXT_OBEY = False

# 并发数
CONCURRENT_REQUESTS = 16
CONCURRENT_REQUESTS_PER_DOMAIN = 8

# 下载延迟
DOWNLOAD_DELAY = 1
RANDOMIZE_DOWNLOAD_DELAY = True

# 超时
DOWNLOAD_TIMEOUT = 30

# 重试
RETRY_ENABLED = True
RETRY_TIMES = 3

# 中间件
DOWNLOADER_MIDDLEWARES = {
    'myspider.middlewares.UserAgentMiddleware': 543,
    'myspider.middlewares.ProxyMiddleware': 544,
}

# 管道
ITEM_PIPELINES = {
    'myspider.pipelines.CsvPipeline': 300,
    # 'myspider.pipelines.MysqlPipeline': 400,
}

# MySQL配置
MYSQL_HOST = 'localhost'
MYSQL_USER = 'root'
MYSQL_PASSWORD = 'password'
MYSQL_DB = 'spider'

# 日志
LOG_LEVEL = 'INFO'
LOG_FILE = 'spider.log'
```

### 第七步：运行爬虫

```bash
# 运行指定爬虫
scrapy crawl product

# 运行并输出到文件
scrapy crawl product -o products.json
scrapy crawl product -o products.csv

# 列出所有爬虫
scrapy list

# 调试（进入shell）
scrapy shell "https://example.com"
```

### 第八步：分布式（Scrapy-Redis）

**安装：**
```bash
pip install scrapy-redis
```

**修改Spider：**
```python
from scrapy_redis.spiders import RedisSpider

class ProductSpider(RedisSpider):
    name = "product"
    redis_key = "product:start_urls"  # 从Redis读取起始URL
    
    def parse(self, response):
        # 和普通Spider一样
        pass
```

**修改settings.py：**
```python
# 使用Redis调度器
SCHEDULER = "scrapy_redis.scheduler.Scheduler"
DUPEFILTER_CLASS = "scrapy_redis.dupefilter.RFPDupeFilter"

# Redis配置
REDIS_URL = 'redis://localhost:6379'

# 管道（去重和存储）
ITEM_PIPELINES = {
    'scrapy_redis.pipelines.RedisPipeline': 300,
}
```

**运行多个爬虫实例：**
```bash
# 机器1
scrapy crawl product

# 机器2
scrapy crawl product

# 推送起始URL到Redis
redis-cli lpush product:start_urls "https://example.com"
```

## 完整代码

```python
# 一个完整的Scrapy爬虫示例
# spiders/quotes_spider.py
import scrapy
from myspider.items import QuoteItem

class QuotesSpider(scrapy.Spider):
    name = "quotes"
    allowed_domains = ["quotes.toscrape.com"]
    start_urls = ["https://quotes.toscrape.com/"]
    
    custom_settings = {
        'DOWNLOAD_DELAY': 1,
        'CONCURRENT_REQUESTS': 4,
    }
    
    def parse(self, response):
        self.logger.info(f"正在解析: {response.url}")
        
        for quote in response.css(".quote"):
            item = QuoteItem()
            item['text'] = quote.css(".text::text").get()
            item['author'] = quote.css(".author::text").get()
            item['tags'] = quote.css(".tag::text").getall()
            yield item
        
        # 下一页
        next_page = response.css(".next a::attr(href)").get()
        if next_page:
            yield response.follow(next_page, self.parse)
```

```python
# items.py
import scrapy

class QuoteItem(scrapy.Item):
    text = scrapy.Field()
    author = scrapy.Field()
    tags = scrapy.Field()
```

## 注意事项

1. **学习曲线** — Scrapy比requests复杂，需要时间学习框架概念
2. **调试** — 用`scrapy shell`调试选择器，非常方便
3. **性能** — Scrapy异步性能好，但要合理设置并发和延迟
4. **反爬** — 配合中间件实现UA轮换、代理、Cookie管理
5. **部署** — 可以用Scrapyd部署，或用Docker容器化

## 进阶拓展

- 学习Scrapy-Redis分布式爬虫
- 了解Scrapyd部署和ScrapydWeb管理
- 学习CrawlSpider（规则爬虫）
- 了解Feed Exports（多种格式导出）
- 学习信号和扩展开发
