---
title: Playwright现代自动化工具入门
date: 2026-10-17 10:00:00
category: 环境配置
tags: [Playwright, 自动化, 浏览器, 动态渲染]
difficulty: 简单
summary: Playwright入门教程，比Selenium更快更稳定，支持多浏览器、自动等待、网络拦截，现代爬虫首选
cover: /images/env-cover.jpg
---

## 适用场景

Selenium太慢或不稳定，需要更现代的浏览器自动化工具。Playwright是微软出品，支持Chrome、Firefox、Safari，自动等待，速度快。

## 实现原理

Playwright通过CDP（Chrome DevTools Protocol）直接控制浏览器，比Selenium的WebDriver协议更快。它内置自动等待机制，不需要手动写等待代码，还支持网络请求拦截、修改响应等高级功能。

## 具体步骤

### 第一步：安装

```bash
pip install playwright
playwright install  # 安装浏览器驱动
```

### 第二步：基础用法（同步API）

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    # 启动浏览器
    browser = p.chromium.launch(headless=True)
    
    # 新建页面
    page = browser.new_page()
    
    # 打开网页
    page.goto("https://example.com")
    
    # 获取标题
    print(page.title())
    
    # 获取HTML
    html = page.content()
    
    # 截图
    page.screenshot(path="screenshot.png")
    
    # 关闭
    browser.close()
```

### 第三步：元素定位与操作

```python
# CSS选择器
page.click(".submit-btn")
page.fill("#username", "admin")
page.fill("#password", "123456")

# 文本选择
page.click("text=登录")
page.click("text=下一页")

# XPath
page.click('//button[@class="submit"]')

# 获取文本
text = page.text_content(".title")

# 获取属性
href = page.get_attribute("a.link", "href")

# 获取多个元素
elements = page.query_selector_all(".item")
for el in elements:
    print(el.text_content())
```

### 第四步：自动等待（核心优势）

```python
# 自动等待元素出现，不需要写WebDriverWait
page.click(".submit-btn")  # 会自动等按钮可点击

# 显式等待
page.wait_for_selector(".content", timeout=10000)
page.wait_for_load_state("networkidle")  # 等待网络空闲
page.wait_for_load_state("domcontentloaded")

# 等待文本出现
page.wait_for_selector("text=加载完成")
```

### 第五步：网络拦截（爬虫神器）

```python
# 拦截请求
def handle_request(route):
    # 修改请求头
    headers = route.request.headers
    headers["User-Agent"] = "Mozilla/5.0..."
    route.continue_(headers=headers)

page.route("**/*", handle_request)

# 拦截响应，直接拿接口数据
def handle_response(response):
    if "/api/data" in response.url:
        data = response.json()
        print("抓到接口数据:", data)

page.on("response", handle_response)
page.goto("https://example.com")
page.wait_for_timeout(5000)
```

### 第六步：反检测配置

```python
browser = p.chromium.launch(
    headless=True,
    args=[
        "--disable-blink-features=AutomationControlled",
        "--no-sandbox",
        "--disable-dev-shm-usage"
    ]
)

context = browser.new_context(
    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    viewport={"width": 1920, "height": 1080},
    locale="zh-CN",
    timezone_id="Asia/Shanghai"
)

# 注入JS隐藏webdriver标识
context.add_init_script("""
    Object.defineProperty(navigator, 'webdriver', {get: () => undefined})
""")
```

## 完整代码

```python
from playwright.sync_api import sync_playwright
import json

class PlaywrightSpider:
    def __init__(self, headless=True):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=headless,
            args=["--disable-blink-features=AutomationControlled"]
        )
        self.context = self.browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            viewport={"width": 1920, "height": 1080}
        )
        self.page = self.context.new_page()
        self.api_data = []
        
        # 监听接口响应
        self.page.on("response", self._capture_api)
    
    def _capture_api(self, response):
        """捕获API接口数据"""
        if "/api/" in response.url:
            try:
                data = response.json()
                self.api_data.append({"url": response.url, "data": data})
            except:
                pass
    
    def fetch(self, url):
        self.page.goto(url, wait_until="networkidle")
        return self.page.content()
    
    def parse(self):
        items = []
        elements = self.page.query_selector_all(".article-item")
        for el in elements:
            items.append({
                "title": el.query_selector(".title").text_content(),
                "url": el.query_selector("a").get_attribute("href")
            })
        return items
    
    def close(self):
        self.browser.close()
        self.playwright.stop()

if __name__ == "__main__":
    spider = PlaywrightSpider(headless=False)
    try:
        spider.fetch("https://example.com")
        data = spider.parse()
        print(f"抓到{len(data)}条数据")
        print(f"捕获{len(spider.api_data)}个API请求")
    finally:
        spider.close()
```

## 注意事项

1. **安装浏览器** — 第一次用必须运行playwright install，不然会报错
2. **同步vs异步** — 简单爬虫用同步API，高并发用异步API（async_playwright）
3. **网络拦截** — page.on("response")是抓接口数据的神器，比解析HTML快得多
4. **自动等待** — Playwright默认自动等待，但动态加载的内容还是要wait_for_selector
5. **资源占用** — 比Selenium轻，但还是要记得close浏览器和context

## 进阶拓展

- 学习Playwright异步API，提高并发效率
- 了解Playwright的代码生成器（playwright codegen）
- 学习使用playwright-stealth绕过检测
- 了解浏览器指纹修改技术
