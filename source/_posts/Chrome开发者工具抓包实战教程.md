---
title: Chrome开发者工具抓包实战教程
date: "2026-10-17 10:10:00"
category: 环境配置
tags: "[Chrome, 开发者工具, 抓包, 调试]"
difficulty: 入门
summary: Chrome DevTools完全教程，Network面板、XHR过滤、请求分析、Cookie查看，爬虫工程师必备技能
cover: https://aka.doubaocdn.com/s/jYS5Rx3Hv0
---

## 适用场景

需要分析网站的请求结构，找到数据接口，查看请求头、参数、响应内容。Chrome开发者工具是最基础也是最重要的抓包工具。

## 实现原理

Chrome开发者工具（DevTools）内置在Chrome浏览器中，可以查看网页加载过程中的所有网络请求，包括请求URL、请求方法、请求头、请求参数、响应头、响应内容等。爬虫工程师通过分析这些请求，找到数据接口并模拟请求。

## 具体步骤

### 第一步：打开开发者工具

三种方式：
1. 按F12
2. 按Ctrl+Shift+I
3. 右键页面 → 检查

打开后切换到 **Network（网络）** 面板。

### 第二步：Network面板基础

**常用按钮：**
- 🔴 录制按钮：开启/关闭请求记录
- 🚫 清除按钮：清空当前请求列表
- 🔍 过滤按钮：显示/隐藏过滤栏
- Preserve log：保留日志（页面跳转不清除）
- Disable cache：禁用缓存

**过滤请求类型：**
- All：全部
- Fetch/XHR：接口请求（最常用）
- JS：JavaScript文件
- CSS：样式文件
- Img：图片
- Media：媒体文件
- Font：字体
- Doc：文档
- WS：WebSocket

**爬虫最常用的是 Fetch/XHR 过滤**，因为数据接口一般都是XHR请求。

### 第三步：分析请求

点击一个请求，右侧会显示详细信息：

**Headers（标头）标签页：**
- General：请求URL、请求方法、状态码、远程地址
- Request Headers：请求头（User-Agent、Cookie、Referer等）
- Response Headers：响应头
- Query String Parameters：GET参数
- Form Data：POST表单参数
- Request Payload：POST JSON参数

**Preview（预览）标签页：**
- 格式化显示响应内容，JSON会自动格式化
- 最常用，用来查看接口返回的数据结构

**Response（响应）标签页：**
- 原始响应内容，未格式化

**Timing（时间）标签页：**
- 请求各阶段耗时，分析性能用

### 第四步：复制请求为代码

找到目标接口后，可以直接复制为代码：

1. 右键请求 → Copy → Copy as cURL (bash)
2. 拿到cURL后，可以用在线工具转成Python代码
3. 或者直接在Postman里导入测试

**复制选项：**
- Copy link address：复制URL
- Copy as cURL (bash)：复制为bash的curl命令
- Copy as cURL (cmd)：复制为Windows cmd的curl命令
- Copy as fetch：复制为JS的fetch代码
- Copy response：复制响应内容

### 第五步：查找数据来源

**方法1：搜索关键词**
1. 在Network面板按Ctrl+F
2. 输入页面上看到的文字（比如文章标题）
3. 会自动搜索所有请求的响应内容
4. 找到包含该文字的请求，就是数据接口

**方法2：XHR过滤**
1. 切换到Fetch/XHR过滤
2. 刷新页面或触发加载
3. 逐个查看请求的Preview，找数据接口

**方法3： Initiator（发起方）**
1. 点击请求的Initiator列
2. 可以看到是哪个JS文件发起的请求
3. 点击可以跳转到Sources面板定位代码

### 第六步：查看Cookie和Storage

**Application（应用）面板：**
- Cookies：查看网站的Cookie
- Local Storage：本地存储
- Session Storage：会话存储
- IndexedDB：索引数据库

**查看Cookie：**
1. 切换到Application面板
2. 左侧Cookies → 选择网站
3. 可以看到所有Cookie的name、value、domain、path、expires

### 第七步：移动端模拟

1. 点击DevTools左上角的手机图标（Ctrl+Shift+M）
2. 可以模拟手机浏览器
3. 顶部可以选择设备型号（iPhone、Android等）
4. 可以模拟网络速度（Slow 3G、Fast 3G等）
5. 很多网站移动端反爬更弱，适合爬虫

## 完整代码

用Chrome分析到接口后，写Python代码模拟请求：

```python
import requests

# 从Chrome复制的请求头
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Referer": "https://example.com/list",
    "Cookie": "your_cookie_here"
}

# 从Chrome分析到的接口参数
params = {
    "page": 1,
    "size": 20,
    "category": "tech"
}

url = "https://api.example.com/v1/articles"
response = requests.get(url, headers=headers, params=params)
data = response.json()

for article in data["data"]["list"]:
    print(f"标题：{article['title']}")
    print(f"链接：{article['url']}")
    print("---")
```

## 注意事项

1. **Preserve log** — 分析跳转页面时一定要勾选，不然页面一跳请求就没了
2. **Disable cache** — 调试时勾选禁用缓存，不然可能拿到旧数据
3. **XHR过滤** — 找数据接口时一定要切到Fetch/XHR，不然请求太多看不过来
4. **请求时序** — 注意请求的先后顺序，有些接口需要先访问某个页面获取Cookie
5. **加密参数** — 如果请求参数是加密的，需要看Initiator定位JS代码进行逆向

## 进阶拓展

- 学习Sources面板断点调试JS
- 了解Performance面板分析页面性能
- 学习使用Charles/Fiddler进行更强大的抓包
- 了解移动端抓包（手机+代理）
