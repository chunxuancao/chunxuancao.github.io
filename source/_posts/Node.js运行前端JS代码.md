---
title: Node.js运行前端JS代码
date: 2026-10-17 14:30:00
category: JS逆向
tags: [Node.js, 扣代码, vm, 执行JS, 中等]
difficulty: 中等
summary: 在Node.js中运行前端JS代码的方法，vm沙箱、eval、模块导出，扣代码后执行加密函数
cover: /images/jsreverse-cover.jpg
---

## 适用场景

已经从网页中扣出了加密函数的JS代码，想在Node.js里运行它来生成签名或加密参数。需要掌握在Node.js中执行前端JS的方法。

## 实现原理

前端JS代码和Node.js代码都是JavaScript，但运行环境不同。前端代码依赖浏览器的全局对象，Node.js有自己的模块系统。可以通过eval、vm沙箱、函数构造器等方式在Node.js中运行前端代码，必要时补全浏览器环境。

## 具体步骤

### 第一步：最简单的方式 - eval

```javascript
const fs = require("fs");

// 读取扣出来的JS代码
const jsCode = fs.readFileSync("encrypt.js", "utf-8");

// 直接eval执行
eval(jsCode);

// 调用全局函数
const result = encrypt("hello");
console.log(result);
```

### 第二步：vm沙箱（推荐）

vm模块可以在独立的沙箱中运行代码，更安全：

```javascript
const fs = require("fs");
const vm = require("vm");

// 读取代码
const jsCode = fs.readFileSync("encrypt.js", "utf-8");

// 创建沙箱上下文
const sandbox = {
    console: console,
    // 可以在这里添加需要的全局对象
    window: {},
    document: {}
};

// 创建上下文
vm.createContext(sandbox);

// 运行代码
vm.runInContext(jsCode, sandbox);

// 调用沙箱中的函数
const result = sandbox.encrypt("hello");
console.log(result);
```

### 第三步：Function构造器

```javascript
const fs = require("fs");

const jsCode = fs.readFileSync("encrypt.js", "utf-8");

// 用Function构造器运行，返回值可以导出
const runner = new Function(`
    ${jsCode}
    return { encrypt: encrypt, decrypt: decrypt };
`);

const { encrypt, decrypt } = runner();
const result = encrypt("hello");
console.log(result);
```

### 第四步：模块导出方式

如果扣的代码比较多，可以改成Node.js模块：

```javascript
// encrypt.js - 改成模块导出
function encrypt(text) {
    // 加密逻辑
    return text;
}

function decrypt(text) {
    // 解密逻辑
    return text;
}

// 导出函数
module.exports = { encrypt, decrypt };
```

```javascript
// 使用
const { encrypt, decrypt } = require("./encrypt.js");
const result = encrypt("hello");
console.log(result);
```

### 第五步：处理全局变量

前端代码经常把函数挂在window上，需要处理：

```javascript
const fs = require("fs");
const vm = require("vm");

const jsCode = fs.readFileSync("encrypt.js", "utf-8");

// 创建window对象，代码会把函数挂在上面
const sandbox = {
    window: {},
    console: console
};
// 让window等于全局对象，这样window.xxx就是全局xxx
sandbox.window = sandbox;

vm.createContext(sandbox);
vm.runInContext(jsCode, sandbox);

// 从window上获取函数
const encrypt = sandbox.window.encrypt || sandbox.encrypt;
const result = encrypt("hello");
console.log(result);
```

### 第六步：处理this指向

前端代码中`this`可能指向window，在Node.js中需要处理：

```javascript
const jsCode = `
    function encrypt(text) {
        return this.prefix + text;
    }
    this.encrypt = encrypt;
`;

// 方式1：用call绑定this
const runner = new Function("window", `
    ${jsCode}
    return window;
`);
const ctx = { prefix: "test_" };
const result = runner.call(ctx, ctx);
console.log(ctx.encrypt("hello"));

// 方式2：在沙箱中this指向sandbox
const vm = require("vm");
const sandbox = { prefix: "test_" };
vm.createContext(sandbox);
vm.runInContext(jsCode, sandbox);
console.log(sandbox.encrypt("hello"));
```

### 第七步：调试技巧

```javascript
const fs = require("fs");
const vm = require("vm");

const jsCode = fs.readFileSync("encrypt.js", "utf-8");

const sandbox = {
    console: console,
    window: {},
    // 添加调试函数
    debug: function(...args) {
        console.log("[DEBUG]", ...args);
    },
    // 打印调用栈
    trace: function() {
        console.log(new Error().stack);
    }
};
sandbox.window = sandbox;

vm.createContext(sandbox);

try {
    vm.runInContext(jsCode, sandbox);
    const result = sandbox.encrypt("hello");
    console.log("结果:", result);
} catch (e) {
    console.log("运行错误:", e.message);
    console.log("错误栈:", e.stack);
}
```

## 完整代码

```javascript
// run.js - 完整的Node.js运行前端JS脚本
const fs = require("fs");
const vm = require("vm");

class JSRunner {
    constructor(code, env = {}) {
        this.code = code;
        this.sandbox = this.createSandbox(env);
    }
    
    createSandbox(env) {
        const sandbox = {
            console: console,
            setTimeout: setTimeout,
            setInterval: setInterval,
            clearTimeout: clearTimeout,
            clearInterval: clearInterval,
            Promise: Promise,
            JSON: JSON,
            Math: Math,
            Date: Date,
            Array: Array,
            Object: Object,
            String: String,
            Number: Number,
            Boolean: Boolean,
            RegExp: RegExp,
            Error: Error,
            ...env
        };
        // window指向自身
        sandbox.window = sandbox;
        sandbox.global = sandbox;
        return sandbox;
    }
    
    run() {
        vm.createContext(this.sandbox);
        try {
            vm.runInContext(this.code, this.sandbox, {
                filename: "spider.js",
                displayErrors: true
            });
            return true;
        } catch (e) {
            console.error("运行错误:", e.message);
            console.error(e.stack);
            return false;
        }
    }
    
    call(funcName, ...args) {
        const func = this.sandbox[funcName] || this.sandbox.window[funcName];
        if (!func) {
            throw new Error(`函数 ${funcName} 不存在`);
        }
        return func.apply(this.sandbox, args);
    }
    
    get(varName) {
        return this.sandbox[varName] || this.sandbox.window[varName];
    }
}

// 使用示例
const code = fs.readFileSync("encrypt.js", "utf-8");
const runner = new JSRunner(code, {
    // 自定义环境变量
    appKey: "your_key",
    appSecret: "your_secret"
});

if (runner.run()) {
    const result = runner.call("encrypt", "hello world");
    console.log("加密结果:", result);
}
```

## 注意事项

1. **环境差异** — 前端代码可能依赖浏览器对象，需要补环境
2. **this指向** — 注意this的指向，前端代码中this可能是window
3. **沙箱安全** — vm沙箱不是完全安全的，恶意代码可能逃逸，不要运行不可信代码
4. **异步代码** — 如果代码有异步操作，需要用Promise或回调处理
5. **调试技巧** — 用console.log在关键位置打印，或者用node --inspect调试

## 进阶拓展

- 学习用node --inspect调试JS代码
- 了解vm2模块，更安全的沙箱
- 学习用puppeteer在真实浏览器运行JS
- 了解WebAssembly在Node.js中的运行
