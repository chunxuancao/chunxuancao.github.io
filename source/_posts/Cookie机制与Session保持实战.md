---
title: Cookie机制与Session保持实战
date: "2026-10-17 11:10:00"
category: 反爬技巧
tags: "[Cookie, Session, 登录态, 反爬, 入门]"
difficulty: 入门
summary: Cookie工作原理、Session保持、登录态维护、Cookie池搭建，需要登录的爬虫必备技能
cover: https://aka.doubaocdn.com/s/1Ht8spUmCQ
---

## 适用场景

网站需要登录才能看到数据，或者不登录只能看少量内容。需要维护登录状态，批量爬取登录后的数据。

## 实现原理

HTTP是无状态协议，Cookie是服务器存在浏览器里的小数据，每次请求自动带上。服务器通过Cookie识别用户身份。爬虫用requests.Session()可以自动保存和发送Cookie，模拟登录状态。

## 具体步骤

### 第一步：Cookie基础

```python
import requests

# 查看响应Cookie
response = requests.get("https://example.com")
print(response.cookies)  # CookieJar对象
print(dict(response.cookies))  # 转成字典

# 手动设置Cookie
cookies = {"session_id": "abc123", "token": "xyz789"}
response = requests.get("https://example.com/user", cookies=cookies)
```

### 第二步：Session自动保持Cookie

```python
# 创建Session，自动管理Cookie
session = requests.Session()

# 第一次请求，服务器设置Cookie
session.get("https://example.com")

# 后续请求自动带上Cookie
response = session.get("https://example.com/user/profile")
print(response.text)  # 已登录状态

# 查看当前所有Cookie
print(dict(session.cookies))
```

### 第三步：模拟登录

```python
def login(username, password):
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Referer": "https://example.com/login"
    })
    
    # 先访问登录页，获取初始Cookie（可能有csrf_token）
    login_page = session.get("https://example.com/login")
    
    # 提交登录表单
    login_data = {
        "username": username,
        "password": password,
        "csrf_token": extract_csrf(login_page.text)  # 从页面提取token
    }
    
    response = session.post("https://example.com/login", data=login_data)
    
    # 检查是否登录成功
    if "退出" in response.text or response.status_code == 200:
        print("登录成功")
        return session
    else:
        print("登录失败")
        return None
```

### 第四步：从浏览器复制Cookie

不想写登录代码时，直接从浏览器复制Cookie：

1. Chrome F12 → Application → Cookies
2. 找到目标网站，复制所有Cookie
3. 转成字典格式

```python
# 浏览器复制的Cookie字符串
cookie_str = "session_id=abc123; token=xyz789; user_id=10086"

# 转成字典
cookies = {}
for item in cookie_str.split("; "):
    key, value = item.split("=", 1)
    cookies[key] = value

# 使用
response = requests.get("https://example.com/user", cookies=cookies)
```

### 第五步：Cookie池（多账号）

需要大量数据时，用多个账号的Cookie轮询，降低单账号被封风险：

```python
import random

class CookiePool:
    def __init__(self):
        self.cookies = []
        self.load_cookies()
    
    def load_cookies(self):
        """从文件加载Cookie池"""
        # 可以从数据库或文件读取
        self.cookies = [
            {"session_id": "aaa", "token": "111"},
            {"session_id": "bbb", "token": "222"},
            {"session_id": "ccc", "token": "333"},
        ]
    
    def get_cookie(self):
        """随机获取一个Cookie"""
        return random.choice(self.cookies)
    
    def remove_cookie(self, cookie):
        """移除失效的Cookie"""
        if cookie in self.cookies:
            self.cookies.remove(cookie)

# 使用
pool = CookiePool()
for i in range(100):
    cookie = pool.get_cookie()
    response = requests.get("https://example.com/data", cookies=cookie)
    if response.status_code == 401:  # Cookie失效
        pool.remove_cookie(cookie)
        cookie = pool.get_cookie()
```

### 第六步：Cookie持久化

把登录后的Cookie保存到文件，下次直接用：

```python
import json

# 保存Cookie
def save_cookies(session, filename="cookies.json"):
    with open(filename, "w") as f:
        json.dump(dict(session.cookies), f)

# 加载Cookie
def load_cookies(filename="cookies.json"):
    with open(filename, "r") as f:
        cookies = json.load(f)
    return cookies

# 使用
session = requests.Session()
session.cookies.update(load_cookies())
```

## 完整代码

```python
import requests
import json
import time

class LoginSpider:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "zh-CN,zh;q=0.9"
        })
        self.cookie_file = "cookies.json"
        self.base_url = "https://example.com"
    
    def login(self, username, password):
        """登录并保存Cookie"""
        # 访问登录页
        self.session.get(f"{self.base_url}/login")
        
        # 提交登录
        data = {"username": username, "password": password}
        response = self.session.post(f"{self.base_url}/login", data=data)
        
        if response.status_code == 200:
            self.save_cookies()
            print("登录成功，Cookie已保存")
            return True
        return False
    
    def save_cookies(self):
        with open(self.cookie_file, "w") as f:
            json.dump(dict(self.session.cookies), f)
    
    def load_cookies(self):
        try:
            with open(self.cookie_file, "r") as f:
                cookies = json.load(f)
            self.session.cookies.update(cookies)
            return True
        except FileNotFoundError:
            return False
    
    def is_logged_in(self):
        """检查是否已登录"""
        response = self.session.get(f"{self.base_url}/user/profile")
        return "退出登录" in response.text
    
    def fetch_data(self, page):
        """爬取登录后的数据"""
        url = f"{self.base_url}/api/data?page={page}"
        response = self.session.get(url)
        if response.status_code == 401:
            print("Cookie失效，需要重新登录")
            return None
        return response.json()

if __name__ == "__main__":
    spider = LoginSpider()
    
    # 先尝试加载已有Cookie
    if spider.load_cookies() and spider.is_logged_in():
        print("使用已保存的Cookie登录成功")
    else:
        print("Cookie失效，重新登录")
        spider.login("username", "password")
    
    # 爬取数据
    for page in range(1, 11):
        data = spider.fetch_data(page)
        if data:
            print(f"第{page}页：{len(data['list'])}条")
        time.sleep(1)
```

## 注意事项

1. **Cookie有效期** — Cookie会过期，过期后需要重新登录，要做好失效检测
2. **不要频繁切换IP** — 同一个Cookie在不同IP使用可能触发安全验证
3. **Cookie保密** — Cookie等于账号密码，不要泄露，不要提交到Git
4. **登录频率** — 不要频繁登录，容易触发账号风控，登录一次用很久
5. **验证码** — 登录时可能有验证码，需要接入打码平台或手动处理

## 进阶拓展

- 学习selenium/playwright自动登录获取Cookie
- 了解JWT Token机制，替代传统Cookie
- 学习使用浏览器扩展导出Cookie
- 了解Cookie的Secure、HttpOnly、SameSite属性
