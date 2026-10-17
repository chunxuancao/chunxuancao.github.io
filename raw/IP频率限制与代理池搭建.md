---
title: IP频率限制与代理池搭建
date: "2026-10-17 11:20:00"
categories:
  - 反爬技巧
tags:
  - 代理池
  - IP代理
  - 频率限制
  - 反爬
  - 中等
difficulty: 中等
summary: IP封禁原理、代理选择、代理池搭建、IP轮换策略，大规模爬虫必备的反封禁技术
cover: https://aka.doubaocdn.com/s/ybj2G5zRPM
---
## 适用场景

爬取速度快了就被封IP，返回403或者需要验证码。需要大量数据时，单IP根本不够用，必须用代理池轮换IP。

## 实现原理

网站通过IP地址识别请求来源，同一IP短时间内大量请求会被判定为爬虫并封禁。代理池维护多个可用代理IP，每次请求随机切换IP，让网站以为是不同用户在访问。

## 具体步骤

### 第一步：检测IP是否被封

```python
import requests

def check_ip_blocked(url):
    """检测IP是否被封"""
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 403:
            return True, "403被封"
        if "访问过于频繁" in response.text:
            return True, "频率限制"
        if "验证" in response.url:
            return True, "跳验证码"
        return False, "正常"
    except Exception as e:
        return True, f"异常: {e}"
```

### 第二步：使用单个代理

```python
# HTTP代理
proxies = {
    "http": "http://127.0.0.1:7890",
    "https": "http://127.0.0.1:7890"
}

# 带认证的代理
proxies = {
    "http": "http://user:password@123.45.67.89:8080",
    "https": "http://user:password@123.45.67.89:8080"
}

response = requests.get("https://httpbin.org/ip", proxies=proxies)
print(response.json())  # 查看当前出口IP
```

### 第三步：代理类型选择

| 代理类型 | 匿名度 | 价格 | 适用场景 |
|---------|-------|------|---------|
| 透明代理 | 最低，会暴露真实IP | 免费 | 不推荐 |
| 匿名代理 | 中等，隐藏真实IP但标识是代理 | 便宜 | 一般反爬 |
| 高匿代理 | 最高，完全隐藏真实IP | 中等 | 推荐 |
| 住宅代理 | 真实家庭宽带IP | 贵 | 强反爬网站 |
| 机房代理 | 数据中心IP | 便宜 | 一般网站 |

### 第四步：简单代理池

```python
import requests
import random

class SimpleProxyPool:
    def __init__(self):
        self.proxies = [
            "http://1.2.3.4:8080",
            "http://5.6.7.8:8080",
            "http://9.10.11.12:8080",
        ]
        self.valid_proxies = []
    
    def validate_proxy(self, proxy):
        """验证代理是否可用"""
        try:
            response = requests.get(
                "https://httpbin.org/ip",
                proxies={"http": proxy, "https": proxy},
                timeout=5
            )
            return response.status_code == 200
        except:
            return False
    
    def get_proxy(self):
        """获取一个可用代理"""
        if not self.valid_proxies:
            self.valid_proxies = [p for p in self.proxies if self.validate_proxy(p)]
        return random.choice(self.valid_proxies) if self.valid_proxies else None

# 使用
pool = SimpleProxyPool()
for i in range(10):
    proxy = pool.get_proxy()
    if proxy:
        response = requests.get(
            "https://example.com/data",
            proxies={"http": proxy, "https": proxy},
            timeout=10
        )
        print(f"第{i}次请求，代理: {proxy}")
```

### 第五步：商用代理API

推荐的代理服务商：
- 快代理、芝麻代理、阿布云（国内）
- Bright Data、Oxylabs、Smartproxy（海外）

```python
class ApiProxyPool:
    def __init__(self, api_url):
        self.api_url = api_url  # 代理提取API
        self.proxy_list = []
        self.index = 0
    
    def fetch_proxies(self):
        """从API提取代理"""
        response = requests.get(self.api_url)
        data = response.json()
        self.proxy_list = [f"http://{item['ip']}:{item['port']}" for item in data['data']]
    
    def get_proxy(self):
        """轮询获取代理"""
        if not self.proxy_list:
            self.fetch_proxies()
        proxy = self.proxy_list[self.index % len(self.proxy_list)]
        self.index += 1
        return proxy
```

### 第六步：IP轮换策略

```python
import time

class SmartSpider:
    def __init__(self):
        self.proxy_pool = SimpleProxyPool()
        self.request_count = 0
        self.current_proxy = None
    
    def fetch(self, url):
        # 每10次请求换一个IP
        if self.request_count % 10 == 0:
            self.current_proxy = self.proxy_pool.get_proxy()
        
        self.request_count += 1
        
        try:
            response = requests.get(
                url,
                proxies={"http": self.current_proxy, "https": self.current_proxy},
                timeout=10
            )
            if response.status_code == 403:
                # 被封了，立即换IP重试
                self.current_proxy = self.proxy_pool.get_proxy()
                return self.fetch(url)
            return response
        except Exception:
            # 代理挂了，换一个重试
            self.current_proxy = self.proxy_pool.get_proxy()
            return self.fetch(url)
```

## 完整代码

```python
import requests
import random
import time
import threading

class ProxyPool:
    def __init__(self, api_url=None):
        self.api_url = api_url
        self.proxies = []
        self.lock = threading.Lock()
    
    def fetch_from_api(self):
        """从代理API获取"""
        if not self.api_url:
            return
        try:
            response = requests.get(self.api_url, timeout=10)
            data = response.json()
            new_proxies = [f"http://{item['ip']}:{item['port']}" for item in data.get('data', [])]
            with self.lock:
                self.proxies.extend(new_proxies)
        except Exception as e:
            print(f"获取代理失败: {e}")
    
    def validate(self, proxy):
        """验证代理"""
        try:
            response = requests.get(
                "https://httpbin.org/ip",
                proxies={"http": proxy, "https": proxy},
                timeout=5
            )
            return response.status_code == 200
        except:
            return False
    
    def get(self):
        """获取可用代理"""
        with self.lock:
            if not self.proxies:
                self.fetch_from_api()
            if not self.proxies:
                return None
            return random.choice(self.proxies)
    
    def remove(self, proxy):
        """移除失效代理"""
        with self.lock:
            if proxy in self.proxies:
                self.proxies.remove(proxy)

class Spider:
    def __init__(self):
        self.proxy_pool = ProxyPool(api_url="your_proxy_api")
        self.headers = {"User-Agent": "Mozilla/5.0"}
        self.max_retries = 3
    
    def fetch(self, url):
        for retry in range(self.max_retries):
            proxy = self.proxy_pool.get()
            try:
                response = requests.get(
                    url,
                    headers=self.headers,
                    proxies={"http": proxy, "https": proxy} if proxy else None,
                    timeout=10
                )
                if response.status_code == 200:
                    return response
                elif response.status_code == 403:
                    self.proxy_pool.remove(proxy)
                    time.sleep(1)
            except Exception as e:
                self.proxy_pool.remove(proxy)
                time.sleep(0.5)
        return None

if __name__ == "__main__":
    spider = Spider()
    for page in range(1, 101):
        response = spider.fetch(f"https://example.com/data?page={page}")
        if response:
            print(f"第{page}页成功")
        time.sleep(random.uniform(0.5, 2))
```

## 注意事项

1. **免费代理慎用** — 免费代理90%不可用，还有安全风险，可能窃取数据
2. **代理质量** — 住宅代理 > 高匿代理 > 普通代理，强反爬网站用住宅代理
3. **并发控制** — 代理也有并发限制，不要同时上百个请求用同一个代理
4. **成本控制** — 代理是按流量或次数收费的，大规模爬取成本不低
5. **法律风险** — 用代理爬取要注意合规，不要爬取敏感数据

## 进阶拓展

- 学习开源代理池项目：proxy_pool、ProxyPool
- 了解adsl拨号代理，自动换IP
- 学习scrapy的代理中间件
- 了解指纹浏览器，配合代理更稳定
