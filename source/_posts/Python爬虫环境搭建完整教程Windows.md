---
title: Python爬虫环境搭建完整教程（Windows）
date: "2026-10-17 09:00:00"
category: 环境配置
tags: "[Python, 环境搭建, Windows, 新手入门]"
difficulty: 入门
summary: 从零开始搭建Python爬虫开发环境，包括Python安装、pip配置、虚拟环境、常用库安装，适合完全零基础的新手
cover: https://aka.doubaocdn.com/s/Uh7X77dvFE
---

## 适用场景

完全零基础的新手，刚接触爬虫，不知道从何开始。或者换了新电脑，需要重新搭建开发环境。

## 实现原理

爬虫开发环境的核心是：Python解释器 + 包管理工具(pip) + 常用爬虫库(requests、BeautifulSoup等) + 代码编辑器。搭建好环境后，才能运行和调试爬虫代码。

## 具体步骤

### 第一步：安装Python

1. 打开Python官网：https://www.python.org/downloads/
2. 下载最新的Python 3.x版本（建议3.10以上）
3. 运行安装程序，**务必勾选"Add Python to PATH"**
4. 选择"Install Now"默认安装
5. 安装完成后，打开cmd，输入 `python --version` 验证

```bash
python --version
# 输出类似：Python 3.11.4
```

### 第二步：配置pip国内源

默认pip下载速度慢，配置国内镜像源：

```bash
# 临时使用国内源
pip install requests -i https://pypi.tuna.tsinghua.edu.cn/simple

# 永久配置（Windows）
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
```

常用国内源：
- 清华：https://pypi.tuna.tsinghua.edu.cn/simple
- 阿里云：https://mirrors.aliyun.com/pypi/simple
- 豆瓣：https://pypi.douban.com/simple

### 第三步：创建虚拟环境（推荐）

虚拟环境可以隔离不同项目的依赖，避免版本冲突：

```bash
# 创建项目文件夹
mkdir my_spider
cd my_spider

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境（Windows）
venv\Scripts\activate

# 激活后命令行前面会有 (venv) 标识
```

### 第四步：安装常用爬虫库

```bash
# 基础请求库
pip install requests

# 网页解析库
pip install beautifulsoup4 lxml

# 自动化工具（需要时再装）
pip install selenium playwright

# 数据存储
pip install pymongo redis openpyxl

# 其他工具
pip install fake-useragent tqdm loguru
```

### 第五步：安装代码编辑器

推荐PyCharm Community（免费）或VS Code：
- PyCharm：https://www.jetbrains.com/pycharm/download/
- VS Code：https://code.visualstudio.com/

## 完整代码

验证环境是否搭建成功，写一个最简单的爬虫：

```python
# test_spider.py
import requests
from bs4 import BeautifulSoup

def test_spider():
    url = "https://httpbin.org/get"
    response = requests.get(url, timeout=10)
    print(f"状态码：{response.status_code}")
    print(f"响应内容：{response.json()}")
    
    # 测试BeautifulSoup
    html = "<html><body><h1>Hello Spider</h1></body></html>"
    soup = BeautifulSoup(html, "lxml")
    print(f"解析结果：{soup.find('h1').text}")

if __name__ == "__main__":
    test_spider()
```

运行：
```bash
python test_spider.py
```

## 注意事项

1. **PATH问题** — 安装Python时一定要勾选Add to PATH，否则cmd里找不到python命令
2. **权限问题** — 如果pip安装报错，用管理员身份运行cmd
3. **虚拟环境** — 新手容易忽略虚拟环境，导致全局环境混乱，建议每个项目单独创建
4. **Python版本** — 不要用Python 2.x，已经停止维护了
5. **网络问题** — pip安装慢就换国内源，不要硬等

## 进阶拓展

- 学习使用conda管理Python环境（适合数据科学方向）
- 配置Docker容器化开发环境
- 了解pyenv多版本Python管理
- 学习使用requirements.txt管理项目依赖
