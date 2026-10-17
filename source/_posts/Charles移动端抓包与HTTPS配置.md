---
title: Charles移动端抓包与HTTPS配置
date: "2026-10-17 10:30:00"
category: 环境配置
tags: "[Charles, 抓包, 移动端, HTTPS, 代理]"
difficulty: 简单
summary: Charles抓包工具教程，重点讲解移动端APP抓包、HTTPS证书配置、SSL代理设置，APP爬虫必备
cover: https://aka.doubaocdn.com/s/5a5NK5Und1
---

## 适用场景

需要抓取手机APP的接口数据，分析APP的请求结构。Charles是跨平台抓包工具，Mac和Windows都能用，移动端抓包体验比Fiddler更好。

## 实现原理

Charles和Fiddler类似，也是HTTP代理服务器，运行在本地8888端口。手机设置代理指向电脑后，所有流量经过Charles，通过安装SSL证书可以解密HTTPS流量。

## 具体步骤

### 第一步：安装与基础配置

1. 下载Charles：https://www.charlesproxy.com/
2. 安装后打开，默认监听8888端口
3. 配置代理端口：Proxy → Proxy Settings → Port: 8888
4. 勾选"Enable transparent HTTP proxying"

### 第二步：电脑端HTTPS配置

1. 安装Charles根证书：
   - Help → SSL Proxying → Install Charles Root Certificate
   - 弹出证书安装窗口，点击"安装证书"
   - 选择"本地计算机" → 下一步
   - 选择"将所有的证书都放入下列存储" → 浏览 → "受信任的根证书颁发机构"
   - 确定 → 完成

2. 启用SSL代理：
   - Proxy → SSL Proxying Settings
   - 勾选"Enable SSL Proxying"
   - 添加规则：Host填`*`，Port填`443`（抓所有HTTPS）
   - 或者只添加需要抓的域名

### 第三步：手机端配置（Android）

1. 手机和电脑连同一个WiFi
2. 查看电脑IP：Help → Local IP Address
3. 手机WiFi设置 → 长按当前WiFi → 修改网络
4. 代理 → 手动
5. 主机名：电脑IP，端口：8888
6. 保存

7. 安装手机端证书：
   - 手机浏览器访问 `chls.pro/ssl`
   - 下载证书文件
   - 安装证书（不同手机位置不同）
     - 小米：设置 → 更多设置 → 系统安全 → 加密与凭据 → 从存储设备安装
     - 华为：设置 → 安全 → 更多安全设置 → 加密和凭据 → 从存储设备安装
     - OPPO/vivo：设置 → 其他设置 → 安全与隐私 → 从存储设备安装证书

8. Android 7.0以上注意：
   - 系统只信任系统级证书，用户安装的证书默认不信任
   - 解决方法1：ROOT手机，把证书放到系统证书目录
   - 解决方法2：APP的targetSdkVersion < 24（老APP）
   - 解决方法3：用VirtualXposed/太极等框架
   - 解决方法4：用Frida Hook绕过SSL校验

### 第四步：手机端配置（iOS）

1. 手机和电脑连同一个WiFi
2. WiFi设置 → HTTP代理 → 手动
3. 服务器：电脑IP，端口：8888
4. 保存

5. 安装证书：
   - Safari访问 `chls.pro/ssl`
   - 下载描述文件
   - 设置 → 通用 → VPN与设备管理 → 安装Charles证书
   - 输入密码确认安装

6. 信任证书（iOS 10.3以上必须）：
   - 设置 → 通用 → 关于本机 → 证书信任设置
   - 找到Charles证书，开启完全信任

### 第五步：Charles界面操作

**会话列表：**
- Structure：按域名结构显示（推荐）
- Sequence：按时间顺序显示

**查看请求详情：**
- Overview：概览
- Request：请求详情（Headers、Cookies、Query、Body）
- Response：响应详情（Headers、Body）
- Summary：摘要
- Notes：备注

**常用功能：**
- 🔍 放大镜：搜索请求内容
- 🎬 录制按钮：开始/停止抓包
- 🔒 锁图标：SSL代理开关
- 🧹 扫帚：清除会话

### 第六步：常用功能

**过滤请求：**
- 左下角Filter框输入域名过滤
- 或者右键域名 → Focus，只显示该域名
- 右键域名 → Hide，隐藏该域名

**修改请求（断点）：**
- Proxy → Breakpoints Settings
- 添加断点规则，勾选Request和Response
- 请求到达时会暂停，可以修改后再放行

**重放请求：**
- 右键请求 → Repeat（重放一次）
- 右键请求 → Repeat Advanced（设置重放次数和并发）
- 右键请求 → Compose（编辑后重放）

**弱网测试：**
- Proxy → Throttle Settings
- 勾选"Enable Throttling"
- 选择网络类型（3G、4G、慢连接等）
- 可以模拟弱网环境测试APP

**Map Local（本地映射）：**
- Tools → Map Local
- 添加规则，把线上请求映射到本地文件
- 适合测试和篡改响应

### 第七步：常见问题排查

**抓不到HTTPS：**
- 检查SSL Proxying是否开启
- 检查证书是否安装并信任
- 检查是否添加了`*:443`规则
- APP是否有SSL Pinning

**手机连不上代理：**
- 检查手机和电脑是否同一WiFi
- 检查电脑防火墙是否放行8888端口
- 检查Charles是否允许局域网连接（Proxy → Proxy Settings → 勾选"Allow remote computers to connect"）

**证书安装后还是抓不到：**
- Android 7+：用户证书不被系统信任，需要ROOT或用框架
- iOS：必须在"证书信任设置"里开启完全信任
- 重启Charles和手机网络

## 完整代码

Charles抓包APP接口后，用Python模拟：

```python
import requests

# 从Charles分析到的APP接口
url = "https://api.app.com/v1/feed"
headers = {
    "User-Agent": "App/3.2.1 (Android 12; SM-G9910)",
    "Accept": "application/json",
    "app-version": "3.2.1",
    "device-id": "your_device_id",
    "token": "your_token",
    "sign": "your_sign"
}
params = {
    "page": 1,
    "count": 20,
    "category": "recommend"
}

# 通过Charles代理调试
proxies = {
    "http": "http://127.0.0.1:8888",
    "https": "http://127.0.0.1:8888"
}

response = requests.get(url, headers=headers, params=params, proxies=proxies, verify=False)
data = response.json()

for item in data["data"]["items"]:
    print(f"标题：{item.get('title', '')}")
    print(f"作者：{item.get('author', '')}")
    print("---")
```

## 注意事项

1. **Android 7+证书问题** — 这是最大的坑，用户安装的证书不被系统信任，很多APP抓不到HTTPS，需要ROOT或Frida
2. **SSL Pinning** — 大厂APP基本都有SSL证书钉扎，即使装了证书也抓不到，需要用Frida Hook绕过
3. **防火墙** — Windows防火墙可能拦截8888端口，手机连不上时先关防火墙测试
4. **证书安全** — Charles证书是全局信任的，用完记得删除，有安全风险
5. **Charles收费** — 免费版每次只能用30分钟，会弹窗提示，可以找破解版或用Fiddler替代

## 进阶拓展

- 学习Frida框架，绕过SSL Pinning和APP反爬
- 了解Xposed/LSPosed框架，Hook APP方法
- 学习mitmproxy，可脚本化的抓包工具
- 了解脱壳技术，获取APP真实代码进行逆向
