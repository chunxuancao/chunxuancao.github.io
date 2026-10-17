---
title: Fiddler抓包工具使用指南
date: 2026-10-17 10:20:00
category: 环境配置
tags: [Fiddler, 抓包, 调试, 代理]
difficulty: 简单
summary: Fiddler抓包工具完全教程，HTTP/HTTPS抓包、请求修改、响应篡改、断点调试，爬虫分析接口必备
cover: /images/env-cover.jpg
---

## 适用场景

Chrome开发者工具不够用，需要更强大的抓包功能，比如修改请求、篡改响应、设置断点、抓取HTTPS流量。Fiddler是Windows上最经典的抓包工具。

## 实现原理

Fiddler是一个HTTP代理服务器，运行在本地8888端口。它把自己设置为系统代理，所有HTTP/HTTPS流量都会经过Fiddler，从而可以捕获、查看、修改请求和响应。

## 具体步骤

### 第一步：安装与配置

1. 下载Fiddler Classic（免费）：https://www.telerik.com/fiddler/fiddler-classic
2. 安装后打开，默认监听8888端口
3. 配置HTTPS抓包：
   - Tools → Options → HTTPS
   - 勾选"Decrypt HTTPS traffic"
   - 弹出证书安装提示，点Yes安装证书
   - 这样就能解密HTTPS流量了

### 第二步：界面介绍

**左侧会话列表（Web Sessions）：**
- #：序号
- Result：状态码
- Protocol：协议（HTTP/HTTPS）
- Host：主机名
- URL：请求路径
- Body：响应大小
- Caching：缓存
- Content-Type：内容类型
- Process：发起进程

**右侧面板：**
- Inspectors：查看请求/响应详情（最常用）
- AutoResponder：自动响应（篡改响应）
- Composer：手动构造请求
- Filters：过滤器
- Statistics：统计信息
- Timeline：时间线

### 第三步：查看请求详情

点击一个会话，右侧Inspectors面板：

**上半部分（请求）：**
- Headers：请求头
- TextView：请求体文本
- WebForms：表单参数
- JSON：JSON参数
- Raw：原始请求
- Cookies：Cookie

**下半部分（响应）：**
- Headers：响应头
- TextView：响应文本
- JSON：JSON响应（自动格式化）
- Image：图片响应
- Raw：原始响应
- HexView：十六进制

### 第四步：过滤请求

**Filters面板：**
1. 勾选"Use Filters"
2. Hosts过滤：只显示指定域名的请求
   - "Show only the following Hosts"：输入域名，如"*.example.com"
3. 状态码过滤：只显示200、404等
4. 内容类型过滤：只显示JSON、HTML等
5. 点击"Actions" → "Run Filterset now"应用

**快速过滤：**
- 左下角黑色区域输入过滤条件
- 如：`@example.com` 只显示example.com的请求
- 如：`=200` 只显示状态码200的请求

### 第五步：修改请求（断点）

**设置断点：**
1. Rules → Automatic Breakpoints → Before Requests（请求前断点）
2. 或者点击左下角状态栏，显示"Before Requests"
3. 此时所有请求会暂停，可以修改

**修改请求：**
1. 点击被断点拦截的请求（红色T图标）
2. 在Inspectors里修改请求头、参数、Cookie
3. 点击"Run to Completion"放行
4. 或者点击"Break on Response"在响应时再断点

**取消断点：**
- Rules → Automatic Breakpoints → Disabled
- 或者点击左下角状态栏直到空白

### 第六步：篡改响应（AutoResponder）

可以让请求返回自定义的响应，不访问真实服务器：

1. 切换到AutoResponder面板
2. 勾选"Enable rules"
3. 点击"Add Rule"
4. 输入匹配规则，如：`https://api.example.com/data`
5. 选择响应：
   - 本地文件：选择一个JSON文件
   - 内置响应：选择"*200-OK"等
   - 拖拽：直接把会话列表里的请求拖进来
6. 刷新页面，请求会返回你设置的响应

### 第七步：重放请求

**Composer面板：**
1. 把会话列表里的请求拖到Composer
2. 修改URL、请求头、请求体
3. 点击"Execute"发送
4. 新的请求会出现在会话列表里

**快捷键：**
- 选中请求按R：重放一次
- 选中请求按Shift+R：重放多次（可设置次数）

### 第八步：手机抓包

1. 手机和电脑连同一个WiFi
2. 查看电脑IP（cmd输入ipconfig）
3. 手机WiFi设置 → 代理 → 手动
4. 主机名填电脑IP，端口填8888
5. 手机浏览器访问 `http://ipv4.fiddler:8888` 下载证书
6. 安装并信任证书
7. 现在手机的HTTP/HTTPS流量都能在Fiddler里看到了

## 完整代码

Fiddler抓包后，用Python模拟请求：

```python
import requests

# 从Fiddler复制的请求信息
url = "https://api.example.com/v1/data"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "application/json",
    "Authorization": "Bearer your_token",
    "Referer": "https://example.com/"
}
params = {
    "page": 1,
    "page_size": 20
}

# 可以设置代理通过Fiddler，方便调试
proxies = {
    "http": "http://127.0.0.1:8888",
    "https": "http://127.0.0.1:8888"
}

response = requests.get(url, headers=headers, params=params, proxies=proxies, verify=False)
print(response.json())
```

## 注意事项

1. **HTTPS证书** — 必须安装并信任Fiddler证书，否则HTTPS抓不到，浏览器会报证书错误
2. **系统代理** — Fiddler会自动设置系统代理，关闭后记得恢复，不然上不了网
3. **过滤很重要** — 不设置过滤的话请求太多，根本看不过来
4. **证书钉扎** — 有些APP做了证书钉扎（SSL Pinning），Fiddler抓不到，需要用Xposed或Frida绕过
5. **Fiddler Everywhere** — 新版Fiddler Everywhere是收费的，用Fiddler Classic免费版就行

## 进阶拓展

- 学习FiddlerScript，用JScript自定义处理逻辑
- 了解Charles（跨平台，Mac用户常用）
- 学习mitmproxy，命令行抓包工具，可脚本化
- 了解Wireshark，更底层的网络抓包
