---
title: RSA加密参数分析与解密
date: "2026-10-17 12:40:00"
category: 反爬技巧
tags: "[RSA, 非对称加密, 公钥, JS逆向, 困难]"
difficulty: 困难
summary: RSA非对称加密原理、公钥提取、Python加密实现、密码加密场景分析，登录接口常用的加密方式
cover: https://aka.doubaocdn.com/s/118YiCy8UF
---

## 适用场景

登录接口的密码是加密的，很长一串，用的是RSA非对称加密。需要找到公钥，用Python复现加密，模拟登录。

## 实现原理

RSA是非对称加密，有公钥和私钥一对。网站把公钥放在前端，前端用公钥加密密码，后端用私钥解密。爬虫只需要拿到公钥，用Python的rsa或cryptography库加密即可，不需要私钥。

## 具体步骤

### 第一步：识别RSA加密

特征：
1. 加密后的密码很长（256位密钥加密后是256字节，Base64后约344字符）
2. 同样的密码每次加密结果不一样（有随机填充）
3. JS里有`JSEncrypt`、`RSAKey`、`encrypt`
4. 页面里有公钥，格式是`-----BEGIN PUBLIC KEY-----`

### 第二步：获取公钥

公钥一般有两种形式：

**形式1：PEM格式**
```
-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQC...
-----END PUBLIC KEY-----
```

**形式2：模和指数**
```javascript
var publicKey = {
    n: "ABCDEF123456...",  // 模数，十六进制
    e: "10001"              // 指数，通常是65537
};
```

获取方式：
1. 直接在JS里搜索`PUBLIC KEY`、`JSEncrypt`
2. 接口返回公钥：`/api/getPublicKey`
3. 写死在JS代码里

### 第三步：分析加密代码

```javascript
// 常见的RSA加密代码
var encrypt = new JSEncrypt();
encrypt.setPublicKey("-----BEGIN PUBLIC KEY-----\n...\n-----END PUBLIC KEY-----");
var encryptedPassword = encrypt.encrypt(password);

// 或者用模和指数
var rsa = new RSAKey();
rsa.setPublic(n, e);
var encryptedPassword = rsa.encrypt(password);
```

### 第四步：Python实现RSA加密

```bash
pip install rsa
# 或者
pip install cryptography
```

**方法1：用rsa库（PEM公钥）**
```python
import rsa
import base64

def rsa_encrypt(plaintext, public_key_pem):
    """RSA加密，PEM格式公钥"""
    public_key = rsa.PublicKey.load_pkcs1_openssl_pem(public_key_pem.encode())
    encrypted = rsa.encrypt(plaintext.encode(), public_key)
    return base64.b64encode(encrypted).decode()

# 使用
public_key = """-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQC...
-----END PUBLIC KEY-----"""

password = "123456"
encrypted = rsa_encrypt(password, public_key)
print(encrypted)
```

**方法2：用cryptography库**
```python
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
import base64

def rsa_encrypt(plaintext, public_key_pem):
    public_key = serialization.load_pem_public_key(
        public_key_pem.encode(),
        backend=default_backend()
    )
    encrypted = public_key.encrypt(
        plaintext.encode(),
        padding.PKCS1v15()  # 注意填充方式
    )
    return base64.b64encode(encrypted).decode()
```

**方法3：用模和指数**
```python
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
import base64

def rsa_encrypt_with_n_e(plaintext, n_hex, e_hex="10001"):
    """用模和指数构造公钥加密"""
    n = int(n_hex, 16)
    e = int(e_hex, 16)
    
    # 构造RSA公钥
    key = RSA.construct((n, e))
    cipher = PKCS1_v1_5.new(key)
    encrypted = cipher.encrypt(plaintext.encode())
    return base64.b64encode(encrypted).decode()
```

### 第五步：填充方式

RSA加密有不同的填充方式，要和JS里一致：
- **PKCS1v15** — 最常用，JSEncrypt默认
- **OAEP** — 更安全，有些网站用
- **NoPadding** — 不填充，很少用

```python
# OAEP填充
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes

encrypted = public_key.encrypt(
    plaintext.encode(),
    padding.OAEP(
        mgf=padding.MGF1(algorithm=hashes.SHA256()),
        algorithm=hashes.SHA256(),
        label=None
    )
)
```

## 完整代码

```python
import requests
import rsa
import base64

class RSALoginSpider:
    def __init__(self):
        self.base_url = "https://example.com"
        self.session = requests.Session()
        self.public_key = None
    
    def get_public_key(self):
        """获取公钥"""
        response = self.session.get(f"{self.base_url}/api/publicKey")
        data = response.json()
        self.public_key = data["publicKey"]
        return self.public_key
    
    def encrypt_password(self, password):
        """RSA加密密码"""
        public_key = rsa.PublicKey.load_pkcs1_openssl_pem(self.public_key.encode())
        encrypted = rsa.encrypt(password.encode(), public_key)
        return base64.b64encode(encrypted).decode()
    
    def login(self, username, password):
        """登录"""
        # 1. 获取公钥
        self.get_public_key()
        
        # 2. 加密密码
        encrypted_password = self.encrypt_password(password)
        
        # 3. 提交登录
        data = {
            "username": username,
            "password": encrypted_password
        }
        response = self.session.post(f"{self.base_url}/api/login", json=data)
        return response.json()

if __name__ == "__main__":
    spider = RSALoginSpider()
    result = spider.login("admin", "123456")
    print(result)
```

## 注意事项

1. **公钥格式** — 注意是PKCS#1还是PKCS#8格式，开头不一样
2. **填充方式** — JSEncrypt默认PKCS1v15，要和Python一致
3. **每次结果不同** — RSA加密有随机填充，同样的明文每次结果不同，这是正常的
4. **分段加密** — 明文太长需要分段，2048位密钥最多加密245字节（PKCS1）
5. **公钥会变** — 有些网站每次请求公钥都不一样，要实时获取

## 进阶拓展

- 学习JSEncrypt库的源码
- 了解RSA的数学原理
- 学习混合加密（RSA+AES）
- 了解国密SM2非对称加密
