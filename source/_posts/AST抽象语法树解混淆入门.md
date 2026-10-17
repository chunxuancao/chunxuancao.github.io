---
title: AST抽象语法树解混淆入门
date: "2026-10-17 14:10:00"
category: JS逆向
tags: "[AST, Babel, 解混淆, 抽象语法树, 困难]"
difficulty: 困难
summary: AST抽象语法树基础，Babel使用教程，自动化解混淆脚本编写，批量处理混淆代码
cover: https://aka.doubaocdn.com/s/hGInNt9mVQ
---

## 适用场景

混淆代码太复杂，手动解混淆效率太低。需要学习AST（抽象语法树），写脚本自动化处理混淆代码，批量还原变量名、字符串、控制流。

## 实现原理

AST（Abstract Syntax Tree，抽象语法树）是代码的树形结构表示。每个节点代表代码中的一个结构（变量声明、函数调用、表达式等）。通过遍历和修改AST节点，可以自动化地进行代码转换，比如解密字符串、重命名变量、还原控制流。Babel是最常用的JS AST处理工具。

## 具体步骤

### 第一步：环境搭建

```bash
# 初始化项目
mkdir deobfuscator
cd deobfuscator
npm init -y

# 安装Babel
npm install @babel/parser @babel/traverse @babel/generator @babel/types
```

### 第二步：AST基础概念

```javascript
// 代码
const a = 1 + 2;

// AST结构（简化）
{
  type: "VariableDeclaration",
  declarations: [{
    type: "VariableDeclarator",
    id: { type: "Identifier", name: "a" },
    init: {
      type: "BinaryExpression",
      operator: "+",
      left: { type: "NumericLiteral", value: 1 },
      right: { type: "NumericLiteral", value: 2 }
    }
  }]
}
```

常用节点类型：
- `Identifier`：标识符（变量名、函数名）
- `StringLiteral`：字符串
- `NumericLiteral`：数字
- `CallExpression`：函数调用
- `FunctionDeclaration`：函数声明
- `VariableDeclaration`：变量声明
- `BinaryExpression`：二元表达式

### 第三步：Babel基本使用

```javascript
const parser = require("@babel/parser");
const traverse = require("@babel/traverse").default;
const generate = require("@babel/generator").default;
const t = require("@babel/types");

// 1. 解析代码为AST
const code = `const a = 1 + 2; console.log(a);`;
const ast = parser.parse(code);

// 2. 遍历AST
traverse(ast, {
    // 访问所有标识符
    Identifier(path) {
        console.log("找到标识符:", path.node.name);
    },
    // 访问所有函数调用
    CallExpression(path) {
        console.log("找到函数调用:", path.node.callee.name);
    }
});

// 3. 生成代码
const output = generate(ast, { compact: false });
console.log(output.code);
```

### 第四步：字符串解密

```javascript
// 混淆代码示例
// var url = _0x1234('0x1');

const fs = require("fs");
const vm = require("vm");

// 1. 读取混淆代码
const obfuscatedCode = fs.readFileSync("obfuscated.js", "utf-8");

// 2. 在沙箱中运行，获取解密函数
const sandbox = {
    window: {},
    document: {},
    navigator: {},
    console: console
};
vm.createContext(sandbox);
vm.runInContext(obfuscatedCode, sandbox);

// 获取解密函数（假设是_0x1234）
const decryptFunc = sandbox._0x1234;

// 3. 解析AST
const ast = parser.parse(obfuscatedCode);

// 4. 遍历，替换所有加密字符串
traverse(ast, {
    CallExpression(path) {
        const { callee, arguments } = path.node;
        // 匹配解密函数调用：_0x1234('0x1')
        if (
            callee.type === "Identifier" &&
            callee.name === "_0x1234" &&
            arguments.length === 1 &&
            arguments[0].type === "StringLiteral"
        ) {
            const key = arguments[0].value;
            try {
                const decrypted = decryptFunc(key);
                // 替换为明文字符串
                path.replaceWith(t.stringLiteral(decrypted));
                console.log("解密:", key, "->", decrypted);
            } catch (e) {
                console.log("解密失败:", key);
            }
        }
    }
});

// 5. 生成解混淆后的代码
const result = generate(ast, { compact: false });
fs.writeFileSync("deobfuscated.js", result.code);
console.log("解混淆完成");
```

### 第五步：常量折叠

把可以计算的表达式直接计算出来：

```javascript
traverse(ast, {
    // 1 + 2 -> 3
    BinaryExpression(path) {
        const { operator, left, right } = path.node;
        if (
            left.type === "NumericLiteral" &&
            right.type === "NumericLiteral"
        ) {
            let result;
            switch (operator) {
                case "+": result = left.value + right.value; break;
                case "-": result = left.value - right.value; break;
                case "*": result = left.value * right.value; break;
                case "/": result = left.value / right.value; break;
                default: return;
            }
            path.replaceWith(t.numericLiteral(result));
        }
    },
    // "a" + "b" -> "ab"
    BinaryExpression(path) {
        const { operator, left, right } = path.node;
        if (
            operator === "+" &&
            left.type === "StringLiteral" &&
            right.type === "StringLiteral"
        ) {
            path.replaceWith(t.stringLiteral(left.value + right.value));
        }
    }
});
```

### 第六步：删除死代码

```javascript
traverse(ast, {
    // if (false) { ... } -> 删除
    IfStatement(path) {
        const { test } = path.node;
        if (test.type === "BooleanLiteral" && test.value === false) {
            // 条件永远为假，删除if，保留else
            if (path.node.alternate) {
                path.replaceWith(path.node.alternate);
            } else {
                path.remove();
            }
        }
    },
    // while (false) { ... } -> 删除
    WhileStatement(path) {
        const { test } = path.node;
        if (test.type === "BooleanLiteral" && test.value === false) {
            path.remove();
        }
    }
});
```

### 第七步：控制流平坦化还原

这是最复杂的部分，需要分析switch-case的跳转逻辑：

```javascript
// 简化版：把switch-case的每个case提取出来
traverse(ast, {
    WhileStatement(path) {
        const { body, test } = path.node;
        // 检查是否是控制流平坦化的while(true) + switch
        if (
            test.type === "BooleanLiteral" &&
            test.value === true &&
            body.body.length === 1 &&
            body.body[0].type === "SwitchStatement"
        ) {
            console.log("找到控制流平坦化");
            // 这里需要复杂的逻辑分析，还原执行顺序
            // 完整实现比较复杂，建议用现成的库
        }
    }
});
```

## 完整代码

```javascript
// deobfuscate.js - 完整的解混淆脚本
const fs = require("fs");
const vm = require("vm");
const parser = require("@babel/parser");
const traverse = require("@babel/traverse").default;
const generate = require("@babel/generator").default;
const t = require("@babel/types");

function deobfuscate(inputFile, outputFile, decryptFuncName) {
    console.log("开始解混淆:", inputFile);
    
    // 1. 读取代码
    const code = fs.readFileSync(inputFile, "utf-8");
    
    // 2. 获取解密函数
    const sandbox = { window: {}, document: {}, navigator: {}, console: console };
    vm.createContext(sandbox);
    try {
        vm.runInContext(code, sandbox);
    } catch (e) {
        console.log("运行警告:", e.message);
    }
    const decryptFunc = sandbox[decryptFuncName];
    
    // 3. 解析AST
    const ast = parser.parse(code, {
        sourceType: "script",
        plugins: []
    });
    
    // 4. 字符串解密
    let decryptedCount = 0;
    traverse(ast, {
        CallExpression(path) {
            const { callee, arguments: args } = path.node;
            if (
                callee.type === "Identifier" &&
                callee.name === decryptFuncName &&
                args.length >= 1 &&
                args[0].type === "StringLiteral"
            ) {
                try {
                    const result = decryptFunc(args[0].value);
                    if (typeof result === "string") {
                        path.replaceWith(t.stringLiteral(result));
                        decryptedCount++;
                    } else if (typeof result === "number") {
                        path.replaceWith(t.numericLiteral(result));
                        decryptedCount++;
                    }
                } catch (e) {}
            }
        }
    });
    console.log("解密字符串:", decryptedCount, "个");
    
    // 5. 常量折叠
    let foldedCount = 0;
    traverse(ast, {
        BinaryExpression(path) {
            const { operator, left, right } = path.node;
            if (
                left.type === "NumericLiteral" &&
                right.type === "NumericLiteral"
            ) {
                let result;
                try {
                    result = eval(`${left.value}${operator}${right.value}`);
                    path.replaceWith(t.numericLiteral(result));
                    foldedCount++;
                } catch (e) {}
            }
        }
    });
    console.log("常量折叠:", foldedCount, "个");
    
    // 6. 生成代码
    const output = generate(ast, {
        compact: false,
        comments: true
    });
    
    fs.writeFileSync(outputFile, output.code);
    console.log("解混淆完成:", outputFile);
}

// 使用
deobfuscate("obfuscated.js", "clean.js", "_0x1234");
```

## 注意事项

1. **先备份** — 解混淆前备份原文件，避免解坏了
2. **沙箱安全** — 运行混淆代码用vm沙箱，避免恶意代码影响系统
3. **控制流复杂** — 控制流平坦化的还原很复杂，建议用现成工具
4. **逐步调试** — 先做字符串解密，再常量折叠，最后控制流还原
5. **测试验证** — 解混淆后要测试代码功能是否正常

## 进阶拓展

- 学习Babel插件开发
- 了解recast、acorn等其他AST工具
- 学习控制流平坦化的完整还原算法
- 了解WebAssembly的逆向分析
