---
title: requests库入门与实战详解
date: "2026-10-17 09:20:00"
categories:
  - 环境配置
tags:
  - requests
  - HTTP
  - 基础
  - 新手入门
difficulty: 入门
summary: requests库完全入门教程，GET/POST请求、请求头、Cookie、Session、文件上传、异常处理，爬虫最基础的库
cover: https://aka.doubaocdn.com/s/Vpqbysrbdc
---
## 适用场景

刚学爬虫，需要掌握最基础的HTTP请求库。requests是Python爬虫最常用的库，90%的爬虫都用它发请求。

## 实现原理

requests是对Python标准库urllib的封装，提供了更简洁的API来发送HTTP请求。它支持GET/POST/PUT/DELETE等所有HTTP方法，自动处理编码、Cookie、连接池等细节。

## 具体步骤

### 第一步：安装

```bash
pip install requests
```

### 第二步：基础GET请求

```python
import requests

# 最简单的GET请求
response = requests.get("https://httpbin.org/get")
print(response.status_code)  # 状态码
print(response.text)         # 文本内容
print(response.json())       # JSON解析
print(response.headers)      # 响应头
print(response.cookies)      # Cookie
```

### 第三步：带参数的GET请求

```python
# 方式1：拼接到URL
response = requests.get("https://httpbin.org/get?name=test&age=18")

# 方式2：params参数（推荐）
params = {"name": "test", "age": 18}
response = requests.get("https://httpbin.org/get", params=params)
print(response.url)  # 自动拼接的URL
```

### 第四步：POST请求

```python
# 表单数据
data = {"username": "admin", "password": "123456"}
response = requests.post("https://httpbin.org/post", data=data)

# JSON数据
json_data = {"username": "admin", "password": "123456"}
response = requests.post("https://httpbin.org/post", json=json_data)
```

### 第五步：请求头设置

```python
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://example.com",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "zh-CN,zh;q=0.9"
}
response = requests.get("https://httpbin.org/get", headers=headers)
```

### 第六步：Session保持登录态

```python
session = requests.Session()

# 登录
login_data = {"username": "admin", "password": "123456"}
session.post("https://example.com/login", data=login_data)

# 后续请求自动带Cookie
response = session.get("https://example.com/user/profile")
print(response.text)
```

### 第七步：异常处理

```python
try:
    response = requests.get("https://httpbin.org/get", timeout=10)
    response.raise_for_status()  # 状态码非200抛出异常
except requests.exceptions.Timeout:
    print("请求超时")
except requests.exceptions.ConnectionError:
    print("连接错误")
except requests.exceptions.HTTPError as e:
    print(f"HTTP错误: {e}")
except requests.exceptions.RequestException as e:
    print(f"请求异常: {e}")
```

## 完整代码

```python
import requests

class BaseSpider:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
    
    def get(self, url, params=None, **kwargs):
        try:
            response = self.session.get(url, params=params, timeout=10, **kwargs)
            response.raise_for_status()
            return response
        except Exception as e:
            print(f"GET请求失败 [{url}]: {e}")
            return None
    
    def post(self, url, data=None, json=None, **kwargs):
        try:
            response = self.session.post(url, data=data, json=json, timeout=10, **kwargs)
            response.raise_for_status()
            return response
        except Exception as e:
            print(f"POST请求失败 [{url}]: {e}")
            return None

if __name__ == "__main__":
    spider = BaseSpider()
    res = spider.get("https://httpbin.org/get", params={"test": "123"})
    if res:
        print(res.json())
```

## 注意事项

1. **编码问题** — response.text可能乱码，用response.content.decode('utf-8')或设置response.encoding
2. **超时必设** — 一定要设timeout，不然请求卡死程序挂住
3. **Session复用** — 多次请求用Session，自动复用连接，速度更快
4. **不要用默认UA** — requests默认UA是python-requests，一看就是爬虫，必被封
5. **SSL证书错误** — 遇到SSL错误可以加verify=False，但有安全风险

## 进阶拓展

- 学习requests的高级用法：流式下载、文件上传、代理设置
- 了解httpx库（支持异步）
- 学习aiohttp异步请求库
- 了解requests的连接池和重试机制
