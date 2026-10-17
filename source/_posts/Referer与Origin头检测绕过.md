---
title: Referer与Origin头检测与绕过
date: "2026-10-17 11:00:00"
category: 反爬技巧
tags: "[Referer, Origin, 请求头, 反爬, 入门]"
difficulty: 入门
summary: Referer和Origin请求头检测原理与绕过方法，防盗链、接口来源验证的处理技巧
cover: https://aka.doubaocdn.com/s/fMnLmDAtqA
---

## 适用场景

请求带了正确的UA还是被拒绝，返回403或者"非法请求"。很多网站会检查Referer或Origin头，验证请求来源是否合法。

## 实现原理

Referer和Origin都是HTTP请求头，用来标识请求的来源页面：
- **Referer**：包含完整的来源URL，比如`https://example.com/list`
- **Origin**：只包含协议+域名，比如`https://example.com`

网站通过检查这两个头，判断请求是从自己的页面发出的，还是外部脚本直接调用的。直接用requests请求时这两个头是空的，容易被识别。

## 具体步骤

### 第一步：检测是否有Referer限制

1. 用Chrome打开目标网站，F12 → Network
2. 找到数据接口请求，查看Request Headers
3. 看是否有Referer或Origin字段
4. 用requests不带这两个头请求测试，如果失败说明有检测

### 第二步：添加Referer头

```python
import requests

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Referer": "https://example.com/list"  # 来源页面URL
}

response = requests.get("https://api.example.com/data", headers=headers)
```

### 第三步：添加Origin头

```python
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Origin": "https://example.com",  # 只需要协议+域名
    "Referer": "https://example.com/list"
}
```

### 第四步：动态生成Referer

爬列表页时，Referer应该是列表页；爬详情页时，Referer应该是列表页或上一级页面：

```python
class RefererSpider:
    def __init__(self):
        self.base_url = "https://example.com"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }
    
    def fetch_list(self, page):
        """爬列表页，Referer设为首页"""
        url = f"{self.base_url}/list?page={page}"
        self.headers["Referer"] = f"{self.base_url}/"
        response = requests.get(url, headers=self.headers)
        return response.text
    
    def fetch_detail(self, article_id, list_page=1):
        """爬详情页，Referer设为来源列表页"""
        url = f"{self.base_url}/article/{article_id}"
        self.headers["Referer"] = f"{self.base_url}/list?page={list_page}"
        response = requests.get(url, headers=self.headers)
        return response.text
```

### 第五步：防盗链图片处理

图片防盗链也是检查Referer，下载图片时需要带Referer：

```python
def download_image(url, referer):
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": referer
    }
    response = requests.get(url, headers=headers, timeout=10)
    if response.status_code == 200:
        with open("image.jpg", "wb") as f:
            f.write(response.content)
        return True
    return False

# 使用
download_image(
    "https://img.example.com/photo.jpg",
    "https://example.com/article/123"
)
```

## 完整代码

```python
import requests
from urllib.parse import urljoin

class AntiRefererSpider:
    def __init__(self, base_url):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9"
        })
    
    def _set_referer(self, path="/"):
        """设置Referer为指定页面"""
        self.session.headers["Referer"] = urljoin(self.base_url, path)
    
    def _set_origin(self):
        """设置Origin头"""
        self.session.headers["Origin"] = self.base_url.rstrip("/")
    
    def fetch_page(self, path, referer="/"):
        """抓取页面，自动设置Referer"""
        self._set_referer(referer)
        url = urljoin(self.base_url, path)
        response = self.session.get(url, timeout=10)
        response.raise_for_status()
        return response.text
    
    def fetch_api(self, api_path, referer="/"):
        """抓取API接口，设置Origin和Referer"""
        self._set_referer(referer)
        self._set_origin()
        url = urljoin(self.base_url, api_path)
        response = self.session.get(url, timeout=10)
        return response.json()
    
    def download_image(self, img_url, referer="/"):
        """下载图片，带Referer防盗链"""
        self._set_referer(referer)
        response = self.session.get(img_url, timeout=15)
        return response.content

if __name__ == "__main__":
    spider = AntiRefererSpider("https://example.com")
    # 先访问首页
    spider.fetch_page("/")
    # 再访问列表页，Referer是首页
    html = spider.fetch_page("/list?page=1", referer="/")
    # 访问API，Referer是列表页
    data = spider.fetch_api("/api/data?page=1", referer="/list?page=1")
    print(data)
```

## 注意事项

1. **Referer要真实** — 不要随便填一个不相关的URL，最好是真实访问过的页面
2. **Origin格式** — Origin只有协议+域名，不要带路径，如`https://example.com`
3. **HTTPS→HTTP** — 从HTTPS页面跳HTTP时，浏览器不会发送Referer，注意这种情况
4. **Referer策略** — 有些网站用meta标签`referrer`控制Referer发送策略，可能只发送域名
5. **不要漏Referer** — 图片、视频、字体等静态资源也可能有防盗链，下载时都要带

## 进阶拓展

- 了解CORS跨域机制和Access-Control-Allow-Origin
- 学习使用浏览器扩展修改请求头
- 了解Referrer-Policy安全头
- 学习mitmproxy批量修改请求头
