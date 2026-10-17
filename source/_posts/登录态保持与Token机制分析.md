---
title: 登录态保持与Token机制分析
date: 2026-10-17 12:10:00
category: 反爬技巧
tags: [Token, JWT, 登录态, 认证, 中等]
difficulty: 中等
summary: Token认证机制、JWT结构分析、Token刷新策略、登录态维护，现代APP和网站常用的认证方式
cover: /images/antibot-cover.jpg
---

## 适用场景

网站不用Cookie认证，而是用Token（如JWT），请求头里带Authorization。需要理解Token机制，维护登录状态，处理Token过期刷新。

## 实现原理

Token是服务器签发的一串字符串，包含用户身份信息和过期时间。客户端登录后拿到Token，后续请求在Header里带上`Authorization: Bearer <token>`。服务器验证Token有效性，不需要像Cookie那样存在服务器Session里。

## 具体步骤

### 第一步：识别Token认证

特征：
1. 请求头里有`Authorization: Bearer xxx`
2. 或者有`token: xxx`、`access-token: xxx`
3. 响应里返回`access_token`、`refresh_token`
4. Cookie里没有session_id

### 第二步：JWT Token结构

JWT（JSON Web Token）由三部分组成，用`.`分隔：
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxMjMsImV4cCI6MTY5OTk5OTk5OX0.abc123...
```

- **Header**：算法和类型，Base64编码
- **Payload**：用户信息和过期时间，Base64编码
- **Signature**：签名，验证Token是否被篡改

```python
import base64
import json

def decode_jwt(token):
    """解码JWT，查看Payload内容"""
    parts = token.split(".")
    if len(parts) != 3:
        return None
    
    # 补全Base64 padding
    def add_padding(s):
        return s + "=" * (4 - len(s) % 4)
    
    # 解码Header
    header = json.loads(base64.urlsafe_b64decode(add_padding(parts[0])))
    # 解码Payload
    payload = json.loads(base64.urlsafe_b64decode(add_padding(parts[1])))
    
    return {"header": header, "payload": payload}

# 使用
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
result = decode_jwt(token)
print(json.dumps(result, indent=2, ensure_ascii=False))
```

### 第三步：登录获取Token

```python
import requests

def login(username, password):
    """登录获取Token"""
    url = "https://api.example.com/auth/login"
    data = {
        "username": username,
        "password": password,
        "grant_type": "password"
    }
    headers = {"Content-Type": "application/json"}
    
    response = requests.post(url, json=data, headers=headers)
    result = response.json()
    
    if "access_token" in result:
        return {
            "access_token": result["access_token"],
            "refresh_token": result.get("refresh_token"),
            "expires_in": result.get("expires_in", 7200)
        }
    else:
        print(f"登录失败: {result}")
        return None
```

### 第四步：请求带Token

```python
def fetch_data(url, token):
    """请求时带Token"""
    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": "Mozilla/5.0"
    }
    response = requests.get(url, headers=headers)
    
    if response.status_code == 401:
        print("Token过期，需要刷新")
        return None
    
    return response.json()
```

### 第五步：Token自动刷新

Token有有效期，过期后用refresh_token刷新：

```python
import time

class TokenManager:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.access_token = None
        self.refresh_token = None
        self.expire_time = 0
        self.base_url = "https://api.example.com"
    
    def login(self):
        """登录获取Token"""
        data = {"username": self.username, "password": self.password}
        response = requests.post(f"{self.base_url}/auth/login", json=data)
        result = response.json()
        
        self.access_token = result["access_token"]
        self.refresh_token = result.get("refresh_token")
        # 提前60秒过期
        self.expire_time = time.time() + result.get("expires_in", 7200) - 60
        print("登录成功")
    
    def refresh(self):
        """刷新Token"""
        data = {"refresh_token": self.refresh_token, "grant_type": "refresh_token"}
        response = requests.post(f"{self.base_url}/auth/refresh", json=data)
        result = response.json()
        
        if "access_token" in result:
            self.access_token = result["access_token"]
            self.expire_time = time.time() + result.get("expires_in", 7200) - 60
            print("Token刷新成功")
            return True
        else:
            print("刷新失败，重新登录")
            self.login()
            return False
    
    def get_token(self):
        """获取有效Token，自动刷新"""
        if not self.access_token:
            self.login()
        elif time.time() > self.expire_time:
            self.refresh()
        return self.access_token
    
    def request(self, method, url, **kwargs):
        """带Token的请求"""
        token = self.get_token()
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {token}"
        
        response = requests.request(method, url, headers=headers, **kwargs)
        
        # 如果401，刷新后重试一次
        if response.status_code == 401:
            self.refresh()
            token = self.get_token()
            headers["Authorization"] = f"Bearer {token}"
            response = requests.request(method, url, headers=headers, **kwargs)
        
        return response
```

### 第六步：Token持久化

```python
import json

def save_token(token_data, filename="token.json"):
    with open(filename, "w") as f:
        json.dump(token_data, f)

def load_token(filename="token.json"):
    try:
        with open(filename, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return None
```

## 完整代码

```python
import requests
import time
import json

class TokenSpider:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.base_url = "https://api.example.com"
        self.token_file = "token.json"
        self.access_token = None
        self.refresh_token = None
        self.expire_time = 0
        self.session = requests.Session()
        self.load_token()
    
    def load_token(self):
        """从文件加载Token"""
        try:
            with open(self.token_file, "r") as f:
                data = json.load(f)
            self.access_token = data.get("access_token")
            self.refresh_token = data.get("refresh_token")
            self.expire_time = data.get("expire_time", 0)
        except:
            pass
    
    def save_token(self):
        """保存Token到文件"""
        data = {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "expire_time": self.expire_time
        }
        with open(self.token_file, "w") as f:
            json.dump(data, f)
    
    def login(self):
        """登录"""
        data = {"username": self.username, "password": self.password}
        response = self.session.post(f"{self.base_url}/auth/login", json=data)
        result = response.json()
        
        self.access_token = result["access_token"]
        self.refresh_token = result.get("refresh_token")
        self.expire_time = time.time() + result.get("expires_in", 7200) - 60
        self.save_token()
    
    def refresh_token(self):
        """刷新Token"""
        data = {"refresh_token": self.refresh_token}
        response = self.session.post(f"{self.base_url}/auth/refresh", json=data)
        result = response.json()
        
        if "access_token" in result:
            self.access_token = result["access_token"]
            self.expire_time = time.time() + result.get("expires_in", 7200) - 60
            self.save_token()
            return True
        return False
    
    def get_headers(self):
        """获取带Token的请求头"""
        if not self.access_token or time.time() > self.expire_time:
            if not self.refresh_token():
                self.login()
        return {"Authorization": f"Bearer {self.access_token}"}
    
    def fetch(self, endpoint, params=None):
        """请求数据"""
        url = f"{self.base_url}{endpoint}"
        headers = self.get_headers()
        response = self.session.get(url, headers=headers, params=params)
        
        if response.status_code == 401:
            self.login()
            headers = self.get_headers()
            response = self.session.get(url, headers=headers, params=params)
        
        return response.json()

if __name__ == "__main__":
    spider = TokenSpider("username", "password")
    for page in range(1, 11):
        data = spider.fetch("/api/data", {"page": page})
        print(f"第{page}页: {len(data.get('list', []))}条")
        time.sleep(1)
```

## 注意事项

1. **Token保密** — Token等于账号密码，不要泄露，不要提交到Git
2. **过期时间** — 注意Token的expires_in，提前刷新，不要等过期了再处理
3. **refresh_token** — refresh_token一般有效期更长，也要保存好
4. **多设备** — 有些网站Token只能一个设备用，频繁换IP可能导致Token失效
5. **签名Token** — 有些Token是动态签名的，每次请求都不一样，需要逆向签名算法

## 进阶拓展

- 学习OAuth2.0认证流程
- 了解JWT的签名验证机制
- 学习分析APP的Token生成算法
- 了解Session和Token的区别与选型
