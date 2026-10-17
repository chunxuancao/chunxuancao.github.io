// ===== Live2D 看板娘 =====
(function () {
  // 加载Live2D库
  const script = document.createElement('script');
  script.src = 'https://cdn.jsdelivr.net/npm/live2d-widget@3.1.4/lib/L2Dwidget.min.js';
  script.onload = function () {
    if (window.L2Dwidget) {
      L2Dwidget.init({
        model: {
          // 二次元少女模型 - 雫(shizuku)
          jsonPath: 'https://cdn.jsdelivr.net/npm/live2d-widget-model-shizuku@1.0.5/assets/shizuku.model.json',
          scale: 1
        },
        display: {
          position: 'left',
          width: 180,
          height: 360,
          hOffset: 10,
          vOffset: -20
        },
        mobile: {
          show: true,
          scale: 0.8
        },
        react: {
          opacity: 0.9,
          opacityDefault: 0.7
        },
        dialog: {
          enable: true,
          script: {
            'tap body': '别摸啦~ 害羞！',
            'tap face': '你好呀~ 我是喵轩的看板娘！',
            'tap head': '摸摸头~',
            'default': '欢迎来到喵轩的技术博客！',
            'mouseover': '想点哪里呀~'
          }
        }
      });
    }
  };
  document.body.appendChild(script);
})();
