---
title: 爬虫反爬之User-Agent检测与绕过
date: "2026-10-17 18:54:37"
category: 反爬技巧
tags: "[User-Agent, 反爬, requests, 新手入门]"
difficulty: 简单
summary: 最常见的反爬机制之一，通过检测User-Agent识别爬虫，本文介绍如何识别和绕过
cover: https://aka.doubaocdn.com/s/R60Un6qSJD
---

## 适用场景

几乎所有网站都会做User-Agent检测，这是最基础也是最常见的反爬手段。当你遇到以下情况时，大概率是UA被检测了：

- 用requests请求返回403 Forbidden
- 用浏览器能正常访问，用Python请求就失败
- 返回的内容和浏览器看到的不一样
- 提示"请使用浏览器访问"

## 实现原理

User-Agent是HTTP请求头里的一个字段，用来标识客户端的浏览器类型、版本、操作系统等信息。网站通过检查这个字段，判断你是真实浏览器还是爬虫脚本。

Python的requests库默认UA是 `python-requests/x.x.x`，一看就是爬虫，所以很多网站直接拦截。

## 具体步骤

### 第一步：获取浏览器的User-Agent

1. 打开浏览器，按F12打开开发者工具
2. 切换到Network面板
3. 刷新页面，随便点一个请求
4. 在Request Headers里找到User-Agent，复制完整内容

常见的UA长这样：
```
Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36
```

### 第二步：在请求中加上UA头

```python
import requests

url = "https://example.com"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

response = requests.get(url, headers=headers)
print(response.status_code)
```

### 第三步：高级用法 - 随机UA

如果请求量大，一直用同一个UA也可能被识别。可以用fake-useragent库随机生成UA：

```python
from fake_useragent import UserAgent
import requests

ua = UserAgent()

for i in range(10):
    headers = {
        "User-Agent": ua.random
    }
    response = requests.get("https://example.com", headers=headers)
    print(headers["User-Agent"])
```

## 完整代码

```python
import requests
from fake_useragent import UserAgent

class UASpider:
    def __init__(self):
        self.ua = UserAgent()
        self.session = requests.Session()
    
    def get_headers(self):
        return {
            "User-Agent": self.ua.random,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive"
        }
    
    def fetch(self, url):
        try:
            response = self.session.get(url, headers=self.get_headers(), timeout=10)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"请求失败: {e}")
            return None

if __name__ == "__main__":
    spider = UASpider()
    html = spider.fetch("https://example.com")
    if html:
        print("请求成功")
```

## 注意事项

1. **不要只用UA头** — 有些网站还会检测Referer、Accept-Language等其他头，尽量把浏览器的所有请求头都复制上
2. **UA要和其他信息匹配** — 别用Windows的UA却传Mac的Accept-Language，容易被识别
3. **fake-useragent可能失效** — 这个库偶尔会因为数据源问题报错，可以自己维护一个UA列表
4. **移动端UA** — 爬移动端网站要用手机的UA，别用桌面的
5. **结合其他反爬手段** — UA只是第一道防线，后面还有Cookie、IP频率、验证码等

## 相关文章

- [爬虫反爬之Cookie检测与绕过](/posts/cookie-detection/)
- [爬虫反爬之IP频率限制与代理池](/posts/ip-rate-limit/)
