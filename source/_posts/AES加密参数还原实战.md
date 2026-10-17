---
title: AES加密参数还原实战
date: "2026-10-17 12:30:00"
category: 反爬技巧
tags: "[AES, 加密, 解密, JS逆向, 困难]"
difficulty: 困难
summary: AES加密原理、ECB/CBC模式、密钥IV提取、Python解密实现，常见的接口数据加密方式
cover: https://aka.doubaocdn.com/s/hnlin8Coz7
---

## 适用场景

接口请求参数或响应数据是加密的，看起来是一串Base64或十六进制字符串。常见于AES加密，需要找到密钥和IV，用Python解密。

## 实现原理

AES是对称加密算法，加密和解密用同一个密钥。常见模式有ECB（最简单，不需要IV）和CBC（需要IV）。网站前端用CryptoJS加密，后端用同样的密钥解密。爬虫需要找到密钥和IV，然后用Python的pycryptodome库解密。

## 具体步骤

### 第一步：识别AES加密

特征：
1. 参数值是Base64编码，长度是16的倍数
2. 或者是十六进制字符串
3. 响应数据也是加密的
4. JS里引入了CryptoJS

常见加密字段：
- `data`、`encrypted_data`、`payload`
- `ciphertext`、`cipher`
- `enc`、`encrypt`

### 第二步：定位加密代码

1. F12 → Sources → 搜索`AES.encrypt`、`CryptoJS.AES`
2. 或者搜索`encrypt`、`decrypt`
3. 在加密函数处打断点
4. 查看输入的明文、密钥、IV

### 第三步：分析加密参数

```javascript
// 常见的AES加密代码
var key = CryptoJS.enc.Utf8.parse("1234567890123456");  // 16位密钥
var iv = CryptoJS.enc.Utf8.parse("1234567890123456");   // 16位IV

// ECB模式（不需要IV）
var encrypted = CryptoJS.AES.encrypt(plaintext, key, {
    mode: CryptoJS.mode.ECB,
    padding: CryptoJS.pad.Pkcs7
});

// CBC模式（需要IV）
var encrypted = CryptoJS.AES.encrypt(plaintext, key, {
    iv: iv,
    mode: CryptoJS.mode.CBC,
    padding: CryptoJS.pad.Pkcs7
});

// 输出Base64
console.log(encrypted.toString());
```

### 第四步：Python解密AES

```bash
pip install pycryptodome
```

```python
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
import base64

def aes_decrypt_ecb(ciphertext_b64, key):
    """AES-ECB解密"""
    key = key.encode("utf-8")
    ciphertext = base64.b64decode(ciphertext_b64)
    
    cipher = AES.new(key, AES.MODE_ECB)
    plaintext = unpad(cipher.decrypt(ciphertext), AES.block_size)
    return plaintext.decode("utf-8")

def aes_decrypt_cbc(ciphertext_b64, key, iv):
    """AES-CBC解密"""
    key = key.encode("utf-8")
    iv = iv.encode("utf-8")
    ciphertext = base64.b64decode(ciphertext_b64)
    
    cipher = AES.new(key, AES.MODE_CBC, iv)
    plaintext = unpad(cipher.decrypt(ciphertext), AES.block_size)
    return plaintext.decode("utf-8")

# 使用
key = "1234567890123456"
iv = "1234567890123456"
encrypted_data = "U2FsdGVkX1..."

# ECB模式
plaintext = aes_decrypt_ecb(encrypted_data, key)
# CBC模式
plaintext = aes_decrypt_cbc(encrypted_data, key, iv)
print(plaintext)
```

### 第五步：Python加密AES

```python
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import base64
import json

def aes_encrypt_ecb(plaintext, key):
    """AES-ECB加密"""
    key = key.encode("utf-8")
    data = pad(plaintext.encode("utf-8"), AES.block_size)
    
    cipher = AES.new(key, AES.MODE_ECB)
    encrypted = cipher.encrypt(data)
    return base64.b64encode(encrypted).decode("utf-8")

def aes_encrypt_cbc(plaintext, key, iv):
    """AES-CBC加密"""
    key = key.encode("utf-8")
    iv = iv.encode("utf-8")
    data = pad(plaintext.encode("utf-8"), AES.block_size)
    
    cipher = AES.new(key, AES.MODE_CBC, iv)
    encrypted = cipher.encrypt(data)
    return base64.b64encode(encrypted).decode("utf-8")

# 使用
data = {"username": "admin", "password": "123456"}
plaintext = json.dumps(data, separators=(',', ':'))
encrypted = aes_encrypt_ecb(plaintext, "1234567890123456")
print(encrypted)
```

### 第六步：密钥查找技巧

密钥可能的位置：
1. 硬编码在JS里（最常见）
2. 从接口动态获取
3. 由某个固定字符串变换而来
4. 和用户ID相关
5. 放在Cookie或LocalStorage里

搜索关键词：`key`、`secret`、`aesKey`、`encryptKey`、`const key`

## 完整代码

```python
import requests
import base64
import json
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

class AESSpider:
    def __init__(self):
        self.base_url = "https://api.example.com"
        self.key = "1234567890123456"  # 从JS里找到的密钥
        self.iv = "1234567890123456"   # 从JS里找到的IV
        self.session = requests.Session()
    
    def encrypt(self, data):
        """加密请求数据"""
        plaintext = json.dumps(data, separators=(',', ':'))
        padded = pad(plaintext.encode("utf-8"), AES.block_size)
        cipher = AES.new(self.key.encode(), AES.MODE_CBC, self.iv.encode())
        encrypted = cipher.encrypt(padded)
        return base64.b64encode(encrypted).decode("utf-8")
    
    def decrypt(self, encrypted_data):
        """解密响应数据"""
        ciphertext = base64.b64decode(encrypted_data)
        cipher = AES.new(self.key.encode(), AES.MODE_CBC, self.iv.encode())
        plaintext = unpad(cipher.decrypt(ciphertext), AES.block_size)
        return json.loads(plaintext.decode("utf-8"))
    
    def request(self, endpoint, data):
        """加密请求，解密响应"""
        url = f"{self.base_url}{endpoint}"
        encrypted_data = self.encrypt(data)
        
        response = self.session.post(url, json={"data": encrypted_data})
        result = response.json()
        
        if result.get("encrypted"):
            return self.decrypt(result["data"])
        return result

if __name__ == "__main__":
    spider = AESSpider()
    result = spider.request("/api/login", {"username": "admin", "password": "123456"})
    print(result)
```

## 注意事项

1. **密钥长度** — AES-128用16位密钥，AES-192用24位，AES-256用32位
2. **模式确认** — ECB不需要IV，CBC需要IV，GCM需要tag，要确认清楚
3. **填充方式** — 常用Pkcs7，也有ZeroPadding，注意区分
4. **编码格式** — 输出可能是Base64或Hex，要对应处理
5. **密钥混淆** — 有些密钥不是明文，需要分析JS里的变换逻辑

## 进阶拓展

- 学习CryptoJS的其他加密算法（DES、3DES、Rabbit）
- 了解AES-GCM模式，带认证标签
- 学习用Node.js直接运行JS加密函数
- 了解国密SM4算法
