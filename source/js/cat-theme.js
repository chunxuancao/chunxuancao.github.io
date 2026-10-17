/* ============================================================
   喵喵小码 · 猫系主题交互脚本
   - 喵叫音效（Web Audio合成，无需外部文件）
   - 猫耳摆动动画
   - 滚动视差
   - 文章卡片入场动画
   ============================================================ */
(function(){
  'use strict';

  /* ── 喵叫音效（Web Audio合成） ── */
  let audioCtx = null;
  function ensureAudio(){
    if(!audioCtx){
      try{
        audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      }catch(e){ return null; }
    }
    if(audioCtx.state === 'suspended') audioCtx.resume();
    return audioCtx;
  }

  function meow(volume){
    volume = volume || 0.12;
    var ctx = ensureAudio();
    if(!ctx) return;
    var now = ctx.currentTime;

    // 喵叫 = 两个音节：升调"喵" + 降调"呜"
    function syllable(start, duration, startFreq, endFreq, vol){
      var osc = ctx.createOscillator();
      var gain = ctx.createGain();
      var filter = ctx.createBiquadFilter();

      osc.type = 'sawtooth';
      osc.frequency.setValueAtTime(startFreq, start);
      osc.frequency.exponentialRampToValueAtTime(endFreq, start + duration * 0.55);
      osc.frequency.exponentialRampToValueAtTime(startFreq * 0.7, start + duration);

      filter.type = 'bandpass';
      filter.frequency.value = 1100;
      filter.Q.value = 4;

      gain.gain.setValueAtTime(0, start);
      gain.gain.linearRampToValueAtTime(vol, start + duration * 0.08);
      gain.gain.linearRampToValueAtTime(vol * 0.5, start + duration * 0.5);
      gain.gain.exponentialRampToValueAtTime(0.001, start + duration);

      osc.connect(filter);
      filter.connect(gain);
      gain.connect(ctx.destination);
      osc.start(start);
      osc.stop(start + duration + 0.05);
    }

    syllable(now, 0.20, 680, 900, volume);
    syllable(now + 0.16, 0.35, 560, 400, volume * 0.85);
  }

  // 暴露到全局，方便其他地方调用
  window.catMeow = meow;

  /* ── 首次交互解锁音频 ── */
  var audioUnlocked = false;
  function unlockAudio(){
    if(audioUnlocked) return;
    audioUnlocked = true;
    ensureAudio();
    document.removeEventListener('click', unlockAudio);
    document.removeEventListener('keydown', unlockAudio);
    document.removeEventListener('touchstart', unlockAudio);
  }
  document.addEventListener('click', unlockAudio);
  document.addEventListener('keydown', unlockAudio);
  document.addEventListener('touchstart', unlockAudio);

  /* ── 点击交互喵叫 ── */
  document.addEventListener('click', function(e){
    // 点击文章卡片
    if(e.target.closest('.recent-post-item')){
      meow(0.08);
      return;
    }
    // 点击导航链接
    if(e.target.closest('#nav a')){
      meow(0.05);
      return;
    }
    // 点击分页
    if(e.target.closest('#pagination a, #pagination .page-number')){
      meow(0.07);
      return;
    }
    // 点击标签/分类
    if(e.target.closest('.tag-cloud a, .category-list a, .article-meta a')){
      meow(0.06);
      return;
    }
    // 点击回到顶部
    if(e.target.closest('#go-up')){
      meow(0.1);
      return;
    }
    // 点击卡片
    if(e.target.closest('.card-widget')){
      meow(0.04);
      return;
    }
  });

  /* ── 导航栏滚动效果 ── */
  var nav = document.getElementById('nav');
  if(nav){
    var lastScroll = 0;
    window.addEventListener('scroll', function(){
      var y = window.scrollY;
      if(y > 60){
        nav.classList.add('fixed');
      }else{
        nav.classList.remove('fixed');
      }
      lastScroll = y;
    }, {passive: true});
  }

  /* ── 文章卡片入场动画 ── */
  if('IntersectionObserver' in window){
    var observer = new IntersectionObserver(function(entries){
      entries.forEach(function(entry){
        if(entry.isIntersecting){
          entry.target.style.opacity = '1';
          entry.target.style.transform = 'translateY(0)';
          observer.unobserve(entry.target);
        }
      });
    }, {threshold: 0.08, rootMargin: '0px 0px -40px 0px'});

    document.querySelectorAll('.recent-post-item, .card-widget, .article-sort-item').forEach(function(el, i){
      el.style.opacity = '0';
      el.style.transform = 'translateY(24px)';
      el.style.transition = 'opacity .7s cubic-bezier(.22,.61,.36,1), transform .7s cubic-bezier(.22,.61,.36,1)';
      el.style.transitionDelay = (i % 4) * 0.06 + 's';
      observer.observe(el);
    });
  }

  /* ── 猫耳随鼠标摆动（导航logo） ── */
  var siteName = document.querySelector('#nav .site-name');
  if(siteName){
    document.addEventListener('mousemove', function(e){
      var rect = siteName.getBoundingClientRect();
      var cx = rect.left + rect.width / 2;
      var dx = (e.clientX - cx) / window.innerWidth;
      var tilt = Math.max(-8, Math.min(8, dx * 16));
      var catEmoji = siteName.querySelector('span') || siteName;
      // 微妙的倾斜跟随
      siteName.style.transform = 'rotate(' + tilt * 0.3 + 'deg)';
      siteName.style.transition = 'transform .2s ease-out';
    });
  }

  /* ── 页面标题喵叫彩蛋 ── */
  var originalTitle = document.title;
  var isPageHidden = false;
  document.addEventListener('visibilitychange', function(){
    if(document.hidden){
      isPageHidden = true;
      document.title = '喵～主人快回来 🐱';
    }else{
      isPageHidden = false;
      document.title = originalTitle;
      meow(0.1);
    }
  });

  /* ── 控制台彩蛋 ── */
  console.log('%c🐱 喵喵小码', 'font-size:24px;font-weight:bold;color:#ff9d5c;text-shadow:0 0 10px rgba(255,157,92,.5);');
  console.log('%c用猫爪写代码的爬虫技术博客', 'font-size:13px;color:#c4b5e0;');
  console.log('%c喵～欢迎来玩！', 'font-size:12px;color:#8a7ab0;');

  /* ── Konami 彩蛋：上下左右 → 全屏喵叫 ── */
  var konamiCode = ['ArrowUp','ArrowUp','ArrowDown','ArrowDown','ArrowLeft','ArrowRight','ArrowLeft','ArrowRight'];
  var konamiIndex = 0;
  document.addEventListener('keydown', function(e){
    if(e.key === konamiCode[konamiIndex]){
      konamiIndex++;
      if(konamiIndex === konamiCode.length){
        konamiIndex = 0;
        // 连续喵叫三次
        meow(0.2);
        setTimeout(function(){ meow(0.18); }, 300);
        setTimeout(function(){ meow(0.22); }, 600);
        // 页面抖动
        document.body.style.animation = 'none';
        document.body.offsetHeight;
        document.body.style.animation = 'catShake .5s ease';
      }
    }else{
      konamiIndex = 0;
    }
  });

  // 注入抖动动画
  var style = document.createElement('style');
  style.textContent = '@keyframes catShake{0%,100%{transform:translateX(0)}20%{transform:translateX(-8px) rotate(-1deg)}40%{transform:translateX(8px) rotate(1deg)}60%{transform:translateX(-5px)}80%{transform:translateX(5px)}}';
  document.head.appendChild(style);

  /* ── Live2D 看板娘（黑猫/白猫，点击切换） ── */
  var catModels = {
    black: 'https://cdn.jsdelivr.net/npm/live2d-widget-model-hijiki@1.0.5/assets/hijiki.model.json',
    white: 'https://cdn.jsdelivr.net/npm/live2d-widget-model-tororo@1.0.5/assets/tororo.model.json'
  };
  var currentCat = 'black';
  var live2dInited = false;

  function initLive2dCat(){
    if(typeof L2Dwidget === 'undefined'){
      setTimeout(initLive2dCat, 500);
      return;
    }
    L2Dwidget.init({
      model: {
        jsonPath: catModels[currentCat],
        scale: 1
      },
      display: {
        position: 'right',
        width: 150,
        height: 200,
        hOffset: 20,
        vOffset: -10
      },
      mobile: {
        show: true
      },
      react: {
        opacity: 0.9
      }
    });
    live2dInited = true;

    // 绑定点击切换
    setTimeout(bindCatClick, 1200);
  }

  function bindCatClick(){
    var widget = document.getElementById('live2d-widget');
    if(!widget) return;
    var canvas = widget.querySelector('canvas');
    if(canvas){
      canvas.style.cursor = 'pointer';
      canvas.addEventListener('click', switchCat);
    }
  }

  function switchCat(){
    // 切换模型
    currentCat = currentCat === 'black' ? 'white' : 'black';
    meow(0.15);
    // 移除旧看板娘
    var widget = document.getElementById('live2d-widget');
    if(widget) widget.remove();
    // 重新初始化
    setTimeout(initLive2dCat, 300);
  }

  initLive2dCat();

})();
