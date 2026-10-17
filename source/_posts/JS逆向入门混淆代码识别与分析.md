---
title: JS逆向入门-混淆代码识别与分析
date: "2026-10-17 13:30:00"
category: JS逆向
tags: "[JS逆向, 混淆, 入门, 调试]"
difficulty: 中等
summary: JS逆向入门教程，混淆代码识别、调试环境搭建、分析思路，爬虫进阶的核心技能
cover: https://aka.doubaocdn.com/s/4CcxUKyx0b
---

## 适用场景

网站的JS代码被混淆了，看不懂，找不到加密函数在哪里。需要学习JS逆向的基本思路和方法，从混淆代码中找到关键逻辑。

## 实现原理

JS逆向就是通过调试和分析，理解混淆后的JavaScript代码逻辑，找到加密、签名、反爬等关键函数的实现，然后用Python复现。核心是利用Chrome开发者工具的断点调试功能，一步步跟踪代码执行。

## 具体步骤

### 第一步：识别混淆类型

常见混淆特征：
1. **变量名无意义** — `a、b、c、_0x1234、_0xabcd`
2. **代码压缩** — 所有代码在一行，没有空格换行
3. **字符串加密** — 字符串都是`\x68\x65\x6c\x6c\x6f`这种形式
4. **控制流平坦化** — 大量switch-case，代码执行顺序混乱
5. **死代码** — 大量没用的代码干扰阅读
6. **调试保护** — 无限debugger、检测开发者工具

### 第二步：搭建调试环境

**Chrome开发者工具：**
- F12打开，Sources面板
- 找到混淆的JS文件
- 点击`{}`（Pretty print）格式化代码
- 格式化后代码会有换行和缩进，方便阅读

**常用快捷键：**
- Ctrl+P：快速打开文件
- Ctrl+Shift+F：全局搜索
- Ctrl+G：跳转到指定行
- F8：继续执行
- F10：单步跳过
- F11：单步进入
- Shift+F11：跳出函数

### 第三步：分析思路

**从结果反推：**
1. 先找到加密后的结果（sign、token等）
2. 搜索这个结果是在哪里生成的
3. 向上追溯调用链
4. 找到核心加密函数

**从输入正推：**
1. 找到请求发出的位置（XHR断点）
2. 单步跟踪参数处理过程
3. 找到加密函数
4. 分析加密算法

**关键词搜索：**
- `encrypt`、`decrypt`、`sign`、`signature`
- `md5`、`sha`、`aes`、`rsa`
- `CryptoJS`、`JSEncrypt`
- `window[`、`eval`、`Function`

### 第四步：XHR断点

XHR断点是最常用的技巧，在请求发出时断住：

1. Sources面板 → XHR/fetch Breakpoints
2. 点击+，输入URL关键词（如`api`）
3. 触发请求，会在send方法处断住
4. 查看调用栈（Call Stack），向上找业务代码
5. 分析参数是怎么处理的

### 第五步：事件断点

有些请求是点击按钮触发的，可以用事件断点：

1. Sources面板 → Event Listener Breakpoints
2. 展开Mouse，勾选click
3. 点击按钮，会在事件处理函数处断住
4. 单步跟踪，找到请求逻辑

### 第六步：函数断点

找到可疑函数后，在行号处点击打断点：
- 蓝色箭头：普通断点
- 条件断点：右键 → Add conditional breakpoint，输入条件
- 日志断点：右键 → Add logpoint，输出日志不暂停

### 第七步：Hook关键函数

用Console注入Hook，监控函数调用：

```javascript
// Hook JSON.stringify
const originalStringify = JSON.stringify;
JSON.stringify = function(...args) {
    console.log("JSON.stringify调用:", args);
    const result = originalStringify.apply(this, args);
    console.log("结果:", result);
    return result;
};

// Hook XMLHttpRequest
const originalOpen = XMLHttpRequest.prototype.open;
XMLHttpRequest.prototype.open = function(method, url) {
    console.log("请求:", method, url);
    return originalOpen.apply(this, arguments);
};
```

## 完整代码

```javascript
// JS逆向分析常用的Hook脚本，在Console中运行

// 1. Hook所有加密相关函数
(function() {
    // Hook MD5
    if (window.md5) {
        const originalMd5 = window.md5;
        window.md5 = function(str) {
            console.log("[MD5] 输入:", str);
            const result = originalMd5(str);
            console.log("[MD5] 输出:", result);
            return result;
        };
    }
    
    // Hook fetch
    const originalFetch = window.fetch;
    window.fetch = function(url, options) {
        console.log("[Fetch] URL:", url);
        console.log("[Fetch] Options:", options);
        return originalFetch.apply(this, arguments).then(response => {
            console.log("[Fetch] Response:", response);
            return response;
        });
    };
    
    // Hook eval（检测代码执行）
    const originalEval = window.eval;
    window.eval = function(code) {
        console.log("[Eval] 执行代码长度:", code.length);
        if (code.length < 500) {
            console.log("[Eval] 代码:", code);
        }
        return originalEval(code);
    };
    
    console.log("Hook已安装");
})();
```

## 注意事项

1. **不要硬读** — 混淆代码不要硬读，用断点调试跟踪执行
2. **格式化代码** — 一定要点Pretty print，不然根本没法看
3. **调用栈很重要** — 断点后先看Call Stack，找到业务代码的位置
4. **多对比** — 对比多次请求的参数变化，找出规律
5. **耐心** — JS逆向需要耐心，复杂的混淆可能要调试很久

## 进阶拓展

- 学习AST抽象语法树解混淆
- 了解常见混淆工具：obfuscator.io、jsfuck、aaencode
- 学习用Node.js运行扣出来的JS代码
- 了解浏览器补环境技术
