---
title: WebAssembly逆向入门
date: "2026-10-17 15:00:00"
category: JS逆向
tags: "[WebAssembly, WASM, 逆向, 困难]"
difficulty: 困难
summary: WebAssembly基础概念，wasm模块分析，函数调用，反编译工具，新一代的代码保护技术
cover: https://aka.doubaocdn.com/s/1rYt4L6U14
---

## 适用场景

网站的加密逻辑放在了WebAssembly（wasm）模块里，JS里看不到具体实现。需要学习分析wasm模块，找到加密函数并调用。

## 实现原理

WebAssembly是一种低级的二进制指令格式，可以在浏览器中高速运行。网站把核心加密逻辑编译成wasm模块，JS只负责调用，这样代码更难被逆向。分析wasm需要用专门的工具查看函数列表，理解参数传递，然后在JS中直接调用wasm的函数。

## 具体步骤

### 第一步：识别WebAssembly

特征：
1. Network面板中有`.wasm`文件
2. JS代码中有`WebAssembly.instantiate`或`WebAssembly.compile`
3. 加密函数调用的是wasm导出的函数
4. 函数名可能是`_encrypt`、`_sign`等（C/C++编译的函数名带下划线）

```javascript
// 加载wasm的典型代码
fetch('crypto.wasm')
    .then(response => response.arrayBuffer())
    .then(bytes => WebAssembly.instantiate(bytes))
    .then(results => {
        const wasm = results.instance.exports;
        // 调用wasm函数
        const result = wasm.encrypt(input);
    });
```

### 第二步：下载wasm文件

1. Network面板找到.wasm文件
2. 右键 → Open in new tab
3. 或者右键 → Save as保存
4. 用工具分析

### 第三步：wasm工具安装

```bash
# 安装wabt（WebAssembly Binary Toolkit）
# 下载：https://github.com/WebAssembly/wabt/releases

# 常用工具
# wasm2wat：把wasm转成文本格式（WAT）
# wat2wasm：把文本转成wasm
# wasm-objdump：查看wasm模块信息
# wasm-decompile：反编译成类C代码
```

### 第四步：查看wasm模块信息

```bash
# 查看导出的函数
wasm-objdump -x crypto.wasm

# 输出示例：
# Section Details:
# Export[6]:
#  - func[0] <memory> -> "memory"
#  - func[1] <encrypt> -> "encrypt"
#  - func[2] <decrypt> -> "decrypt"
#  - func[3] <malloc> -> "malloc"
#  - func[4] <free> -> "free"
```

### 第五步：反编译成WAT文本

```bash
# 转成文本格式
wasm2wat crypto.wasm -o crypto.wat

# 查看WAT文件
cat crypto.wat
```

WAT格式示例：
```lisp
(module
  (func $encrypt (param $0 i32) (param $1 i32) (result i32)
    (local $2 i32)
    (local.set $2
      (i32.add
        (local.get $0)
        (local.get $1)
      )
    )
    (local.get $2)
  )
  (memory (export "memory") 1)
  (export "encrypt" (func $encrypt))
)
```

### 第六步：反编译成类C代码

```bash
# 用wasm-decompile反编译
wasm-decompile crypto.wasm -o crypto.dec.c
```

输出示例：
```c
// 类C代码，比WAT容易读
int encrypt(int a, int b) {
    return a + b;
}
```

### 第七步：在JS中调用wasm函数

```javascript
// 加载并调用wasm
async function callWasm() {
    const response = await fetch('crypto.wasm');
    const bytes = await response.arrayBuffer();
    const { instance } = await WebAssembly.instantiate(bytes);
    const wasm = instance.exports;
    
    // 简单参数（数字）
    const result = wasm.encrypt(123, 456);
    console.log('结果:', result);
    
    // 字符串参数需要先写入内存
    const str = "hello";
    const encoder = new TextEncoder();
    const strBytes = encoder.encode(str);
    
    // 分配内存（如果wasm导出了malloc）
    const ptr = wasm.malloc(strBytes.length);
    
    // 写入内存
    const memory = new Uint8Array(wasm.memory.buffer);
    memory.set(strBytes, ptr);
    
    // 调用函数，传入指针和长度
    const resultPtr = wasm.encrypt(ptr, strBytes.length);
    
    // 读取结果
    const resultBytes = memory.slice(resultPtr, resultPtr + 32);
    const resultStr = new TextDecoder().decode(resultBytes);
    console.log('结果:', resultStr);
}
```

### 第八步：内存操作详解

wasm和JS之间传递复杂数据（字符串、数组）需要通过内存：

```javascript
class WasmHelper {
    constructor(instance) {
        this.wasm = instance.exports;
        this.memory = new Uint8Array(this.wasm.memory.buffer);
    }
    
    // 字符串写入wasm内存，返回指针
    writeString(str) {
        const encoder = new TextEncoder();
        const bytes = encoder.encode(str);
        const ptr = this.wasm.malloc(bytes.length + 1);
        const memory = new Uint8Array(this.wasm.memory.buffer);
        memory.set(bytes, ptr);
        memory[ptr + bytes.length] = 0;  // null终止
        return ptr;
    }
    
    // 从wasm内存读取字符串
    readString(ptr, length) {
        const memory = new Uint8Array(this.wasm.memory.buffer);
        const bytes = memory.slice(ptr, ptr + length);
        return new TextDecoder().decode(bytes);
    }
    
    // 读取以null结尾的字符串
    readCString(ptr) {
        const memory = new Uint8Array(this.wasm.memory.buffer);
        let end = ptr;
        while (memory[end] !== 0) end++;
        const bytes = memory.slice(ptr, end);
        return new TextDecoder().decode(bytes);
    }
}
```

### 第九步：高级工具

**在线工具：**
- https://wasmexplorer.com/ — 在线wasm分析
- https://webassembly.github.io/wabt/demo/wasm2wat/ — 在线转WAT

**专业工具：**
- **Ghidra** + wasm插件 — 强大的逆向工具
- **IDA Pro** + wasm插件 — 专业逆向
- **wasm3** — 解释器，可以调试
- **binaryen** — wasm优化和处理工具

## 完整代码

```javascript
// wasm-caller.js - 完整的wasm调用封装

class WasmCrypto {
    constructor(wasmUrl) {
        this.wasmUrl = wasmUrl;
        this.instance = null;
        this.exports = null;
    }
    
    async init() {
        const response = await fetch(this.wasmUrl);
        const bytes = await response.arrayBuffer();
        const { instance } = await WebAssembly.instantiate(bytes, {
            // 导入环境（如果wasm需要）
            env: {
                memory: new WebAssembly.Memory({ initial: 256 }),
                abort: () => console.log('abort'),
            }
        });
        this.instance = instance;
        this.exports = instance.exports;
        console.log('wasm加载完成，导出函数:', Object.keys(this.exports));
        return this;
    }
    
    // 写入字符串到内存
    writeString(str) {
        const encoder = new TextEncoder();
        const bytes = encoder.encode(str);
        const ptr = this.exports.malloc(bytes.length + 1);
        const memory = new Uint8Array(this.exports.memory.buffer);
        memory.set(bytes, ptr);
        memory[ptr + bytes.length] = 0;
        return { ptr, length: bytes.length };
    }
    
    // 读取字符串
    readString(ptr, length) {
        const memory = new Uint8Array(this.exports.memory.buffer);
        const bytes = memory.slice(ptr, ptr + length);
        return new TextDecoder().decode(bytes);
    }
    
    // 调用加密函数
    encrypt(plaintext) {
        const { ptr, length } = this.writeString(plaintext);
        const resultPtr = this.exports.encrypt(ptr, length);
        // 假设返回32位MD5
        const result = this.readString(resultPtr, 32);
        this.exports.free(ptr);
        this.exports.free(resultPtr);
        return result;
    }
    
    // 调用签名函数
    sign(params) {
        const jsonStr = JSON.stringify(params);
        const { ptr, length } = this.writeString(jsonStr);
        const resultPtr = this.exports.sign(ptr, length);
        const result = this.readString(resultPtr, 64);
        this.exports.free(ptr);
        this.exports.free(resultPtr);
        return result;
    }
}

// 使用
(async () => {
    const crypto = new WasmCrypto('crypto.wasm');
    await crypto.init();
    
    const encrypted = crypto.encrypt('hello world');
    console.log('加密结果:', encrypted);
    
    const sign = crypto.sign({ user: 'admin', time: 123456 });
    console.log('签名:', sign);
})();
```

## 注意事项

1. **函数名修饰** — C/C++编译的函数名可能带下划线`_encrypt`，Rust编译的可能更复杂
2. **内存管理** — wasm的内存需要手动管理，malloc后要free，避免内存泄漏
3. **参数类型** — wasm只支持i32、i64、f32、f64等基本类型，复杂数据通过内存传递
4. **工具选择** — 简单的用wabt，复杂的用Ghidra/IDA
5. **动态调试** — wasm也可以在Chrome里调试，Sources面板会显示wasm的代码

## 进阶拓展

- 学习用Ghidra逆向wasm模块
- 了解wasm的安全沙箱机制
- 学习Rust/C++编译到wasm
- 了解wasm的SIMD和多线程特性
