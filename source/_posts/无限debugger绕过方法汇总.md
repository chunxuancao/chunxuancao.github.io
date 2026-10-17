---
title: 无限debugger绕过方法汇总
date: "2026-10-17 14:50:00"
category: JS逆向
tags: "[debugger, 反调试, 绕过, JS逆向]"
difficulty: 中等
summary: 无限debugger原理，多种绕过方法，Never pause here、定时器Hook、AST删除，反调试技巧汇总
cover: https://aka.doubaocdn.com/s/MunIXf1j0m
---

## 适用场景

打开开发者工具后，页面不断弹出debugger，无法正常调试。这是网站的反调试手段，需要学会绕过无限debugger。

## 实现原理

无限debugger是网站的反调试手段，通过定时器或循环不断执行`debugger`语句，当开发者工具打开时，代码会在debugger处暂停，导致无法正常调试。绕过的核心是让debugger语句不执行或者不暂停。

## 具体步骤

### 第一步：识别无限debugger

特征：
1. 打开F12后，代码不断在debugger处暂停
2. Sources面板显示`debugger`语句
3. 按F8继续后马上又断住
4. 关闭开发者工具页面正常运行

常见形式：
```javascript
// 形式1：定时器
setInterval(function() {
    debugger;
}, 100);

// 形式2：循环
while (true) {
    debugger;
}

// 形式3：函数递归
function debug() {
    debugger;
    setTimeout(debug, 100);
}
debug();

// 形式4：构造器
(function() {
    return debugger;
})();

// 形式5：混淆的debugger
(function() {
    var _0x1234 = function() {
        return 'debugger';
    };
    (function() {
        new Function(_0x1234())();
    })();
})();
```

### 第二步：方法1 - Never pause here

最简单的方法：

1. 在debugger语句的行号上右键
2. 选择"Never pause here"
3. 这一行永远不会暂停
4. 按F8继续

**适用场景：** debugger在固定的一行，比较简单

### 第三步：方法2 - 禁用所有断点

1. Sources面板 → 点击停用断点按钮（ octagon）
2. 或者按Ctrl+F8
3. 所有断点都不会生效，包括debugger
4. 调试完再开启

**缺点：** 自己打的断点也不生效了

### 第四步：方法3 - Hook定时器

如果是setInterval/setTimeout触发的debugger：

```javascript
// 在Console中运行
// 保存原函数
const origSetInterval = window.setInterval;
const origSetTimeout = window.setTimeout;

// 重写setInterval
window.setInterval = function(fn, time) {
    // 检查函数内容是否包含debugger
    if (fn.toString().includes('debugger')) {
        console.log('拦截到debugger定时器');
        return null;  // 不执行
    }
    return origSetInterval.apply(this, arguments);
};

// 重写setTimeout
window.setTimeout = function(fn, time) {
    if (fn.toString().includes('debugger')) {
        console.log('拦截到debugger延时器');
        return null;
    }
    return origSetTimeout.apply(this, arguments);
};

console.log('定时器Hook已安装');
```

**注意：** 要在debugger代码执行之前运行Hook，可以用Overrides替换JS文件，在最前面加Hook代码。

### 第五步：方法4 - Hook Function构造器

如果debugger是通过`new Function('debugger')()`执行的：

```javascript
// Hook Function构造器
const origFunction = window.Function;
window.Function = function(...args) {
    // 检查参数是否包含debugger
    const code = args.join('');
    if (code.includes('debugger')) {
        console.log('拦截到Function构造器debugger');
        return function() {};  // 返回空函数
    }
    return new origFunction(...args);
};
window.Function.prototype = origFunction.prototype;
```

### 第六步：方法5 - Hook eval

如果debugger是通过eval执行的：

```javascript
const origEval = window.eval;
window.eval = function(code) {
    if (typeof code === 'string' && code.includes('debugger')) {
        console.log('拦截到eval debugger');
        // 移除debugger语句
        code = code.replace(/debugger/g, '');
    }
    return origEval(code);
};
```

### 第七步：方法6 - 用Overrides替换JS

最彻底的方法，直接修改JS文件：

1. Sources面板 → Overrides → 选择本地文件夹
2. 找到包含debugger的JS文件
3. 右键 → Save for overrides
4. 编辑文件，删除所有debugger语句
5. 保存，刷新页面

**优点：** 彻底解决，可以修改任意代码
**缺点：** 需要找到所有debugger的位置

### 第八步：方法7 - AST批量删除

用AST工具批量删除debugger语句：

```javascript
const parser = require("@babel/parser");
const traverse = require("@babel/traverse").default;
const generate = require("@babel/generator").default;
const fs = require("fs");

const code = fs.readFileSync("obfuscated.js", "utf-8");
const ast = parser.parse(code);

// 删除所有debugger语句
traverse(ast, {
    DebuggerStatement(path) {
        path.remove();
    }
});

const result = generate(ast, { compact: false });
fs.writeFileSync("clean.js", result.code);
console.log("已删除所有debugger语句");
```

### 第九步：方法8 - 时间差检测绕过

有些代码用时间差检测开发者工具：

```javascript
// 检测代码
(function() {
    var start = new Date();
    debugger;
    var end = new Date();
    if (end - start > 100) {
        // 开发者工具打开了
        location.href = 'about:blank';
    }
})();
```

绕过方法：
1. 用Never pause here让debugger不暂停
2. 或者Hook Date，让时间差很小
3. 或者直接删除检测代码

## 完整代码

```javascript
// anti-debugger.js - 完整的反调试绕过脚本
// 在页面加载前运行，或者用Overrides注入

(function() {
    console.log('安装反调试绕过...');
    
    // 1. Hook setInterval
    const origSetInterval = window.setInterval;
    window.setInterval = function(fn, time) {
        try {
            if (fn && fn.toString && fn.toString().includes('debugger')) {
                console.log('[拦截] setInterval debugger');
                return null;
            }
        } catch(e) {}
        return origSetInterval.apply(this, arguments);
    };
    
    // 2. Hook setTimeout
    const origSetTimeout = window.setTimeout;
    window.setTimeout = function(fn, time) {
        try {
            if (fn && fn.toString && fn.toString().includes('debugger')) {
                console.log('[拦截] setTimeout debugger');
                return null;
            }
        } catch(e) {}
        return origSetTimeout.apply(this, arguments);
    };
    
    // 3. Hook Function构造器
    const origFunction = window.Function;
    window.Function = function(...args) {
        try {
            const code = args.join('');
            if (code.includes('debugger')) {
                console.log('[拦截] Function debugger');
                return function() {};
            }
        } catch(e) {}
        return new origFunction(...args);
    };
    window.Function.prototype = origFunction.prototype;
    
    // 4. Hook eval
    const origEval = window.eval;
    window.eval = function(code) {
        try {
            if (typeof code === 'string' && code.includes('debugger')) {
                console.log('[拦截] eval debugger');
                code = code.replace(/debugger/g, '');
            }
        } catch(e) {}
        return origEval(code);
    };
    
    console.log('反调试绕过安装完成');
})();
```

## 注意事项

1. **时机很重要** — Hook代码要在debugger代码执行之前运行，用Overrides在最前面注入
2. **多种方式组合** — 有些网站用多种反调试手段，需要组合使用
3. **不要在Console运行** — Console运行时debugger可能已经开始了，要用Overrides
4. **检测绕过** — 有些网站会检测setInterval是否被Hook，需要更隐蔽的方式
5. **升级反调试** — 现在的网站可能用更复杂的反调试，需要具体分析

## 进阶拓展

- 学习浏览器扩展注入脚本，在页面加载前运行Hook
- 了解更多反调试手段：控制台检测、窗口大小检测、内存检测
- 学习用puppeteer的自动化操作绕过反调试
- 了解WebAssembly中的反调试
