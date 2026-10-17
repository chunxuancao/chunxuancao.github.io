---
title: 常见JS混淆类型与解混淆方法
date: "2026-10-17 14:00:00"
category: JS逆向
tags: "[混淆, 解混淆, obfuscator, JS逆向]"
difficulty: 中等
summary: 常见JS混淆类型识别，变量混淆、字符串加密、控制流平坦化、死代码，以及对应的解混淆方法
cover: https://aka.doubaocdn.com/s/UKMR9eKuPk
---

## 适用场景

拿到的JS代码完全看不懂，各种乱码和无意义变量。需要识别混淆类型，用对应的方法还原代码，方便分析。

## 实现原理

JS混淆是通过各种技术手段让代码变得难以阅读，但功能不变。常见的混淆手段包括：变量名替换、字符串加密、控制流平坦化、死代码插入、调试保护等。解混淆就是逆向这些操作，还原代码的可读性。

## 具体步骤

### 第一步：变量名混淆

**特征：**
- 变量名都是`a、b、c、_0x1234`
- 函数名无意义
- 没有任何语义

**解混淆方法：**
- 格式化代码（Pretty print）
- 重命名变量（Rename symbol）：右键变量 → Rename symbol
- 根据上下文推断变量含义，手动重命名
- 用AST工具批量重命名

### 第二步：字符串加密

**特征：**
```javascript
// 加密前
var url = "https://api.example.com";

// 加密后
var url = _0x1234('0x12');  // 通过函数解密
// 或者
var url = '\x68\x74\x74\x70\x73';  // 十六进制
// 或者
var url = atob('aHR0cHM6Ly9hcGkuZXhhbXBsZS5jb20=');  // Base64
```

**解混淆方法：**
1. 找到解密函数
2. 在Console中运行解密函数，批量解密字符串
3. 用AST工具替换所有加密字符串

```javascript
// 在Console中运行解密函数
console.log(_0x1234('0x12'));  // 输出解密后的字符串

// 批量解密
for (let i = 0; i < 100; i++) {
    const key = '0x' + i.toString(16);
    try {
        console.log(key, '=', _0x1234(key));
    } catch(e) {}
}
```

### 第三步：控制流平坦化

**特征：**
```javascript
// 正常代码
function test(a, b) {
    if (a > b) return a;
    else return b;
}

// 平坦化后
function test(a, b) {
    var _0x1234 = '0x1';
    while (true) {
        switch (_0x1234) {
            case '0x1':
                if (a > b) _0x1234 = '0x2';
                else _0x1234 = '0x3';
                continue;
            case '0x2':
                return a;
            case '0x3':
                return b;
        }
        break;
    }
}
```

**解混淆方法：**
- 用AST工具还原控制流
- 在线工具：https://tool.lu/js/
- 开源工具：obfuscator-io-deobfuscator
- 简单的可以手动分析switch-case的跳转逻辑

### 第四步：死代码

**特征：**
- 大量永远不会执行的代码
- 无意义的条件判断
- 干扰阅读的垃圾代码

```javascript
function test() {
    var a = 1;
    if (false) {  // 永远不会执行
        doSomething();
    }
    while (1 > 2) {  // 永远不会执行
        doSomething();
    }
    return a;
}
```

**解混淆方法：**
- 用AST工具删除死代码
- 手动分析，删除明显不会执行的分支
- 用代码压缩工具自动删除

### 第五步：调试保护

**特征：**
- 无限debugger
- 检测开发者工具是否打开
- 检测窗口大小变化
- 时间差检测

```javascript
// 无限debugger
setInterval(function() {
    debugger;
}, 100);

// 检测开发者工具
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

**解混淆方法：**
- 右键debugger行 → Never pause here
- 用浏览器扩展禁用debugger
- Hook相关函数
- 用AST删除调试保护代码

### 第六步：常见混淆工具识别

| 混淆工具 | 特征 |
|---------|------|
| obfuscator.io | `_0x`开头变量，字符串数组，控制流平坦化 |
| jsfuck | 只有`[]()!+`六个字符 |
| aaencode | 只有颜文字`(^_^)`等 |
| jjencode | 只有`$`和符号 |
| UglifyJS | 变量名短，代码压缩 |
| Terser | 类似UglifyJS，ES6+ |

### 第七步：在线解混淆工具

推荐工具：
1. **https://tool.lu/js/** — 在线JS格式化和解混淆
2. **https://deobfuscate.io/** — obfuscator.io专用
3. **https://lelinhtinh.github.io/de4js/** — 多种混淆格式
4. **https://github.com/relative/synchrony** — obfuscator.io解混淆工具

## 完整代码

```javascript
// 简单的字符串解密脚本，在Console中运行

// 假设解密函数是 _0x1234
function decryptAllStrings(decryptFunc, start = 0, end = 200) {
    const results = {};
    for (let i = start; i < end; i++) {
        const key = '0x' + i.toString(16);
        try {
            const value = decryptFunc(key);
            if (value && typeof value === 'string') {
                results[key] = value;
            }
        } catch(e) {}
    }
    console.table(results);
    return results;
}

// 使用：decryptAllStrings(_0x1234, 0, 100);

// 禁用无限debugger
(function() {
    const origSetInterval = window.setInterval;
    window.setInterval = function(fn, time) {
        if (fn.toString().includes('debugger')) {
            console.log('拦截到debugger定时器');
            return null;
        }
        return origSetInterval.apply(this, arguments);
    };
    
    // 禁用debugger关键字
    Object.defineProperty(window, 'debugger', {
        set: function() {},
        get: function() { return undefined; }
    });
})();
```

## 注意事项

1. **先格式化** — 任何混淆代码先Pretty print，不然根本没法看
2. **不要硬读** — 混淆代码不要硬读，用工具和断点辅助
3. **在线工具有限** — 复杂的混淆在线工具解不了，需要手动分析
4. **字符串解密** — 先把字符串解密了，代码可读性会大幅提升
5. **保留原文件** — 解混淆前备份原文件，避免解坏了

## 进阶拓展

- 学习AST抽象语法树，写自己的解混淆工具
- 了解Babel插件开发，自动化解混淆
- 学习obfuscator.io的混淆原理
- 了解WebAssembly混淆
