---
title: MD5与SHA签名逆向分析
date: 2026-10-17 12:50:00
category: 反爬技巧
tags: [MD5, SHA, 哈希, 签名, JS逆向, 中等]
difficulty: 中等
summary: MD5/SHA哈希算法原理、签名参数分析、盐值查找、Python复现，最常见的接口签名算法
cover: /images/antibot-cover.jpg
---

## 适用场景

接口有sign参数，是32位（MD5）或40位（SHA1）或64位（SHA256）的十六进制字符串。需要分析签名规则，找到盐值，用Python复现。

## 实现原理

MD5和SHA都是哈希算法，把任意长度的输入转成固定长度的输出。网站常用它们做接口签名：把请求参数按一定规则拼接，加上密钥（盐值），然后哈希得到sign。服务器用同样的方式计算，对比是否一致。

## 具体步骤

### 第一步：识别哈希类型

根据签名长度判断：
- **32位十六进制** → MD5（最常见）
- **40位十六进制** → SHA1
- **64位十六进制** → SHA256
- **128位十六进制** → SHA512

```python
def detect_hash(sign):
    """根据长度判断哈希类型"""
    length = len(sign)
    if length == 32:
        return "MD5"
    elif length == 40:
        return "SHA1"
    elif length == 64:
        return "SHA256"
    elif length == 128:
        return "SHA512"
    else:
        return "Unknown"
```

### 第二步：定位签名代码

1. F12 → Sources → 搜索`md5`、`sha1`、`sha256`、`sign`
2. 或者XHR断点，在请求发出时断住
3. 查看调用栈，找到生成sign的函数
4. 在函数入口打断点，查看输入参数

### 第三步：分析签名规则

常见的签名模式：

**模式1：参数排序+拼接+盐值**
```javascript
function generateSign(params) {
    var keys = Object.keys(params).sort();
    var str = "";
    keys.forEach(function(key) {
        str += key + "=" + params[key] + "&";
    });
    str += "key=your_secret";  // 盐值
    return md5(str);
}
```

**模式2：时间戳+盐值**
```javascript
function generateSign() {
    var timestamp = Date.now();
    var sign = md5(timestamp + "salt_value");
    return {timestamp: timestamp, sign: sign};
}
```

**模式3：HMAC**
```javascript
function generateSign(params, secret) {
    var str = JSON.stringify(params);
    return CryptoJS.HmacSHA256(str, secret).toString();
}
```

**模式4：多层哈希**
```javascript
function generateSign(str) {
    return md5(sha1(md5(str)));  // 多层嵌套
}
```

### 第四步：查找盐值（密钥）

盐值可能的位置：
1. 硬编码在JS里（搜索`secret`、`key`、`salt`、`appkey`）
2. 从接口动态获取
3. 由用户ID和固定字符串组合
4. 放在Cookie或LocalStorage里
5. 经过混淆或变换

**技巧：**
- 用已知的参数和sign，反推可能的盐值
- 对比多次请求，找出不变的部分
- 在加密函数处断点，查看拼接后的完整字符串

### 第五步：Python复现

```python
import hashlib
import time
import json
import hmac

def md5_sign(params, salt="your_secret"):
    """MD5签名：参数排序+拼接+盐值"""
    sorted_params = sorted(params.items())
    str_list = [f"{k}={v}" for k, v in sorted_params]
    sign_str = "&".join(str_list) + f"&key={salt}"
    return hashlib.md5(sign_str.encode()).hexdigest()

def sha1_sign(params, salt="your_secret"):
    """SHA1签名"""
    sorted_params = sorted(params.items())
    str_list = [f"{k}={v}" for k, v in sorted_params]
    sign_str = "&".join(str_list) + f"&key={salt}"
    return hashlib.sha1(sign_str.encode()).hexdigest()

def sha256_sign(params, salt="your_secret"):
    """SHA256签名"""
    sorted_params = sorted(params.items())
    str_list = [f"{k}={v}" for k, v in sorted_params]
    sign_str = "&".join(str_list) + f"&key={salt}"
    return hashlib.sha256(sign_str.encode()).hexdigest()

def hmac_sha256_sign(params, secret="your_secret"):
    """HMAC-SHA256签名"""
    str_data = json.dumps(params, separators=(',', ':'))
    return hmac.new(
        secret.encode(),
        str_data.encode(),
        hashlib.sha256
    ).hexdigest()

def timestamp_sign(salt="your_secret"):
    """时间戳+MD5签名"""
    timestamp = str(int(time.time() * 1000))
    sign = hashlib.md5((timestamp + salt).encode()).hexdigest()
    return timestamp, sign
```

### 第六步：验证签名

用已知的输入输出测试Python复现是否正确：

```python
def verify_sign():
    """验证签名算法是否正确"""
    # 从浏览器抓到的已知数据
    test_params = {"a": "1", "b": "2"}
    known_sign = "已知的sign值"
    salt = "your_secret"
    
    # 用Python计算
    calculated_sign = md5_sign(test_params, salt)
    
    if calculated_sign == known_sign:
        print("签名算法正确！")
        return True
    else:
        print(f"不匹配，计算值: {calculated_sign}，已知值: {known_sign}")
        return False
```

## 完整代码

```python
import requests
import hashlib
import time
import json

class HashSignSpider:
    def __init__(self):
        self.base_url = "https://api.example.com"
        self.app_key = "your_app_key"
        self.app_secret = "your_app_secret"
        self.session = requests.Session()
    
    def generate_sign(self, params):
        """生成MD5签名"""
        # 添加公共参数
        params["app_key"] = self.app_key
        params["timestamp"] = str(int(time.time()))
        params["nonce"] = hashlib.md5(str(time.time()).encode()).hexdigest()[:8]
        
        # 参数排序
        sorted_params = sorted(params.items())
        # 拼接
        sign_str = "&".join([f"{k}={v}" for k, v in sorted_params])
        sign_str += f"&app_secret={self.app_secret}"
        
        # MD5签名，转大写（有些网站要大写）
        sign = hashlib.md5(sign_str.encode()).hexdigest().upper()
        params["sign"] = sign
        return params
    
    def request(self, endpoint, data=None):
        """带签名的请求"""
        url = f"{self.base_url}{endpoint}"
        params = data or {}
        signed_params = self.generate_sign(params)
        
        response = self.session.get(url, params=signed_params)
        return response.json()

if __name__ == "__main__":
    spider = HashSignSpider()
    result = spider.request("/api/data", {"page": 1, "size": 20})
    print(json.dumps(result, indent=2, ensure_ascii=False))
```

## 注意事项

1. **大小写** — 有些网站要大写MD5，有些要小写，注意区分
2. **参数顺序** — 排序方式很重要，有些按ASCII排序，有些按参数名排序
3. **拼接格式** — 注意是`key=value&`还是`keyvalue`，有没有分隔符
4. **盐值位置** — 盐值可能在开头、中间或结尾，要仔细看JS
5. **编码问题** — 中文参数要注意URL编码，和JS里的编码方式一致

## 进阶拓展

- 学习用彩虹表破解简单的MD5
- 了解HMAC的原理和实现
- 学习分析混淆的JS签名代码
- 了解加盐哈希的安全性
