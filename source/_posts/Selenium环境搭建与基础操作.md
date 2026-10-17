---
title: Selenium环境搭建与基础操作
date: "2026-10-17 09:50:00"
categories:
  - 环境配置
tags:
  - Selenium
  - 自动化
  - 浏览器
  - 动态渲染
difficulty: 简单
summary: Selenium4环境搭建与基础操作，驱动配置、元素定位、等待机制、无头模式，处理JS渲染页面必备
cover: https://aka.doubaocdn.com/s/UFwz8FDa5l
---
## 适用场景

目标网站是JS动态渲染的，requests拿到的HTML里没有数据，需要用真实浏览器渲染页面后再提取。Selenium是最经典的浏览器自动化工具。

## 实现原理

Selenium通过WebDriver控制真实浏览器（Chrome、Firefox等），模拟人的操作打开网页、点击、输入、滚动，等JS渲染完成后再获取页面内容。

## 具体步骤

### 第一步：安装

```bash
pip install selenium
```

Selenium4内置了驱动管理器，不需要手动下载chromedriver了。

### 第二步：基础用法

```python
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

# 配置浏览器
chrome_options = Options()
chrome_options.add_argument("--headless")  # 无头模式（不显示窗口）
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--window-size=1920,1080")

# 启动浏览器
driver = webdriver.Chrome(options=chrome_options)

# 打开网页
driver.get("https://example.com")

# 获取页面标题
print(driver.title)

# 获取渲染后的HTML
html = driver.page_source

# 关闭浏览器
driver.quit()
```

### 第三步：元素定位

```python
from selenium.webdriver.common.by import By

# 8种定位方式
driver.find_element(By.ID, "username")
driver.find_element(By.NAME, "password")
driver.find_element(By.CLASS_NAME, "btn")
driver.find_element(By.TAG_NAME, "input")
driver.find_element(By.LINK_TEXT, "下一页")
driver.find_element(By.PARTIAL_LINK_TEXT, "下一页")
driver.find_element(By.XPATH, '//div[@class="content"]')
driver.find_element(By.CSS_SELECTOR, ".content > h1")

# 找多个元素
elements = driver.find_elements(By.XPATH, '//li[@class="item"]')
```

### 第四步：元素操作

```python
# 输入文本
input_box = driver.find_element(By.ID, "username")
input_box.send_keys("admin")

# 清空输入框
input_box.clear()

# 点击按钮
button = driver.find_element(By.CLASS_NAME, "submit")
button.click()

# 获取文本
text = element.text

# 获取属性
href = element.get_attribute("href")

# 提交表单
form.submit()
```

### 第五步：等待机制（重要）

```python
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# 显式等待（推荐）
wait = WebDriverWait(driver, 10)
element = wait.until(
    EC.presence_of_element_located((By.CLASS_NAME, "content"))
)

# 常用等待条件
EC.title_is("标题")
EC.url_contains("keyword")
EC.element_to_be_clickable((By.ID, "btn"))
EC.text_to_be_present_in_element((By.CLASS_NAME, "status"), "完成")

# 隐式等待（全局）
driver.implicitly_wait(10)

# 强制等待（不推荐）
import time
time.sleep(3)
```

### 第六步：高级操作

```python
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

# 鼠标悬停
ActionChains(driver).move_to_element(element).perform()

# 右键点击
ActionChains(driver).context_click(element).perform()

# 双击
ActionChains(driver).double_click(element).perform()

# 拖拽
ActionChains(driver).drag_and_drop(source, target).perform()

# 滚动到元素
driver.execute_script("arguments[0].scrollIntoView();", element)

# 执行JS
driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

# 切换iframe
driver.switch_to.frame("iframe_id")
driver.switch_to.default_content()  # 切回主页面

# 切换标签页
driver.switch_to.window(driver.window_handles[1])

# 处理弹窗
alert = driver.switch_to.alert
alert.accept()  # 确认
alert.dismiss()  # 取消
```

## 完整代码

```python
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

class SeleniumSpider:
    def __init__(self, headless=True):
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)
    
    def fetch(self, url):
        self.driver.get(url)
        # 等待内容加载
        self.wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, "content"))
        )
        return self.driver.page_source
    
    def parse_list(self):
        items = []
        articles = self.driver.find_elements(By.XPATH, '//div[@class="article"]')
        for article in articles:
            title = article.find_element(By.XPATH, './/h2').text
            url = article.find_element(By.XPATH, './/a').get_attribute("href")
            items.append({"title": title, "url": url})
        return items
    
    def close(self):
        self.driver.quit()

if __name__ == "__main__":
    spider = SeleniumSpider(headless=False)
    try:
        spider.fetch("https://example.com")
        data = spider.parse_list()
        for item in data:
            print(item)
    finally:
        spider.close()
```

## 注意事项

1. **驱动版本** — Selenium4自动管理驱动，但Chrome版本太旧可能有问题，保持Chrome最新
2. **等待很重要** — 不要用time.sleep，用显式等待，不然页面没加载完就提取会报错
3. **无头模式检测** — 很多网站能检测headless，需要加反检测参数或用undetected-chromedriver
4. **资源占用** — Selenium很吃内存，爬完记得driver.quit()，不要只close()
5. **iframe** — 元素在iframe里时必须先switch_to.frame，不然找不到

## 进阶拓展

- 学习undetected-chromedriver，绕过反爬检测
- 了解Playwright，比Selenium更快更现代
- 学习Selenium的分布式Grid
- 了解浏览器指纹反检测技术
