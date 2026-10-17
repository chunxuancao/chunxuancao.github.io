---
title: Chrome断点调试高级技巧
date: 2026-10-17 13:40:00
category: JS逆向
tags: [Chrome, 断点调试, DevTools, 技巧]
difficulty: 中等
summary: Chrome开发者工具断点调试高级技巧，条件断点、日志断点、DOM断点、事件断点，JS逆向必备技能
cover: /images/jsreverse-cover.jpg
---

## 适用场景

已经会基础的断点调试，但遇到混淆代码还是找不到关键逻辑。需要掌握更高级的断点技巧，快速定位加密函数。

## 实现原理

Chrome开发者工具提供了多种断点类型，可以在特定条件、特定事件、特定DOM变化时暂停代码执行。通过组合使用这些断点，可以快速定位到关键代码的执行位置，而不用一步步单步跟踪。

## 具体步骤

### 第一步：基础断点

**普通断点：**
- 点击行号，出现蓝色箭头
- 代码执行到这一行会暂停

**条件断点（Conditional Breakpoint）：**
- 右键行号 → Add conditional breakpoint
- 输入条件表达式，如`user.id === 123`
- 只有条件为true时才暂停
- 适合在循环中找特定情况

**日志断点（Logpoint）：**
- 右键行号 → Add logpoint
- 输入日志表达式，如`"参数:", param`
- 不会暂停，只在Console输出日志
- 适合观察变量变化不中断执行

### 第二步：XHR/fetch断点

在请求发出时暂停：

1. Sources面板 → XHR/fetch Breakpoints
2. 点击+，输入URL关键词
3. 如输入`api`，所有包含`api`的请求都会断住
4. 断住后查看Call Stack，向上找业务代码

**技巧：**
- 输入空字符串会拦截所有请求
- 可以添加多个断点规则
- 断点会在XMLHttpRequest.send或fetch调用处暂停

### 第三步：DOM断点

在DOM元素变化时暂停：

1. Elements面板 → 选中元素
2. 右键 → Break on
3. 三种类型：
   - **Subtree modifications**：子节点变化时
   - **Attributes modifications**：属性变化时
   - **Node removal**：节点被删除时

**适用场景：**
- 验证码图片加载时
- 弹窗出现时
- 页面内容动态变化时

### 第四步：事件断点

在特定事件触发时暂停：

1. Sources面板 → Event Listener Breakpoints
2. 展开事件类别，勾选需要的事件
3. 常用事件：
   - Mouse → click（点击时）
   - Keyboard → keydown（按键时）
   - Control → resize（窗口大小变化）
   - Load → load（页面加载）
   - Timer → setTimeout（定时器）

**技巧：**
- 点击按钮前勾选click，点击后会在事件处理函数处断住
- 可以快速找到按钮的点击事件处理函数

### 第五步：异常断点

在代码抛出异常时暂停：

1. Sources面板 → 点击暂停按钮（ octagon）
2. 勾选"Pause on caught exceptions"可以在捕获的异常处也暂停
3. 适合找代码报错的位置

### 第六步：调试时的常用操作

**查看变量：**
- Scope面板：查看当前作用域的变量
- Watch面板：添加要监视的变量表达式
- Console：直接输入变量名查看
- 鼠标悬停在变量上：显示变量值

**调用栈（Call Stack）：**
- 显示函数调用链
- 点击任意帧可以跳转到对应代码
- 可以查看每个函数的参数和局部变量
- 右键 → Restart frame可以重新执行该函数

**单步操作：**
- F8 / Resume：继续执行
- F10 / Step over：单步跳过（不进入函数）
- F11 / Step into：单步进入（进入函数）
- Shift+F11 / Step out：跳出当前函数
- 右键行号 → Continue to here：执行到这一行

### 第七步：黑盒脚本（Blackbox）

把不想调试的脚本加入黑盒，单步时不会进入：

1. Settings → Ignore List
2. 添加脚本URL模式，如`*jquery*`
3. 或者在Call Stack中右键脚本 → Add to ignore list
4. 单步调试时会跳过这些库代码

**常用黑盒：**
- jQuery、React、Vue等框架
- 统计、广告脚本
- 不需要分析的第三方库

### 第八步：Snippets代码片段

保存常用的调试脚本，随时运行：

1. Sources面板 → Snippets → New snippet
2. 写代码，Ctrl+Enter运行
3. 可以保存Hook脚本、解密函数等

```javascript
// 常用Snippet：Hook所有请求
(function() {
    const origOpen = XMLHttpRequest.prototype.open;
    XMLHttpRequest.prototype.open = function(method, url) {
        console.log('[XHR]', method, url);
        this.addEventListener('load', function() {
            console.log('[XHR Response]', url, this.responseText.substring(0, 200));
        });
        return origOpen.apply(this, arguments);
    };
    console.log('XHR Hook已安装');
})();
```

## 完整代码

```javascript
// JS逆向调试常用Snippet合集

// 1. 查找所有包含关键词的函数
function findFunctions(keyword) {
    const results = [];
    for (const key in window) {
        try {
            if (typeof window[key] === 'function' && 
                window[key].toString().includes(keyword)) {
                results.push(key);
            }
        } catch(e) {}
    }
    console.log(`找到${results.length}个包含"${keyword}"的函数:`, results);
    return results;
}

// 2. 监控对象属性变化
function watchProperty(obj, prop) {
    const descriptor = Object.getOwnPropertyDescriptor(obj, prop);
    let value = obj[prop];
    Object.defineProperty(obj, prop, {
        get() {
            console.trace(`读取 ${prop}:`, value);
            return value;
        },
        set(newVal) {
            console.trace(`设置 ${prop}:`, value, '->', newVal);
            value = newVal;
        }
    });
}

// 3. 函数调用栈追踪
function traceFunction(obj, funcName) {
    const orig = obj[funcName];
    obj[funcName] = function(...args) {
        console.trace(`调用 ${funcName}:`, args);
        const result = orig.apply(this, args);
        console.log(`返回 ${funcName}:`, result);
        return result;
    };
}

// 使用示例
// findFunctions('encrypt');
// watchProperty(window, 'token');
// traceFunction(JSON, 'stringify');
```

## 注意事项

1. **断点太多会慢** — 不要同时开太多断点，页面会卡
2. **黑盒很重要** — 把第三方库加入黑盒，不然单步会进入库代码
3. **条件断点技巧** — 条件里可以写任意JS，包括console.log
4. **调用栈向上找** — XHR断点后一般在库代码里，要向上找业务代码
5. **刷新后断点还在** — Chrome会保存断点，不用每次重新设置

## 进阶拓展

- 学习Performance面板分析代码性能
- 了解Memory面板分析内存泄漏
- 学习用Overrides替换线上JS文件
- 了解Chrome DevTools Protocol，自动化调试
