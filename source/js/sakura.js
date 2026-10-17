// ===== 樱花飘落特效 =====
(function () {
  const canvas = document.createElement('canvas');
  canvas.id = 'sakura-canvas';
  document.body.appendChild(canvas);
  const ctx = canvas.getContext('2d');

  let width = canvas.width = window.innerWidth;
  let height = canvas.height = window.innerHeight;

  window.addEventListener('resize', () => {
    width = canvas.width = window.innerWidth;
    height = canvas.height = window.innerHeight;
  });

  // 樱花花瓣类
  class Sakura {
    constructor() {
      this.reset();
    }

    reset() {
      this.x = Math.random() * width;
      this.y = -20;
      this.size = Math.random() * 10 + 6;
      this.speedY = Math.random() * 1.5 + 0.8;
      this.speedX = Math.random() * 1.5 - 0.75;
      this.angle = Math.random() * Math.PI * 2;
      this.angleSpeed = Math.random() * 0.03 + 0.01;
      this.opacity = Math.random() * 0.5 + 0.5;
      this.rotate = Math.random() * Math.PI * 2;
    }

    update() {
      this.y += this.speedY;
      this.x += this.speedX + Math.sin(this.angle) * 0.8;
      this.angle += this.angleSpeed;
      this.rotate += 0.02;

      if (this.y > height + 20 || this.x < -20 || this.x > width + 20) {
        this.reset();
      }
    }

    draw() {
      ctx.save();
      ctx.translate(this.x, this.y);
      ctx.rotate(this.rotate);
      ctx.globalAlpha = this.opacity;

      // 画樱花花瓣（五瓣）
      ctx.fillStyle = '#ffb7c5';
      for (let i = 0; i < 5; i++) {
        ctx.beginPath();
        const petalAngle = (i * 2 * Math.PI) / 5;
        const px = Math.cos(petalAngle) * this.size * 0.5;
        const py = Math.sin(petalAngle) * this.size * 0.5;
        ctx.ellipse(px, py, this.size * 0.4, this.size * 0.25, petalAngle, 0, Math.PI * 2);
        ctx.fill();
      }

      // 花心
      ctx.fillStyle = '#ff8fab';
      ctx.beginPath();
      ctx.arc(0, 0, this.size * 0.15, 0, Math.PI * 2);
      ctx.fill();

      ctx.restore();
    }
  }

  // 创建樱花
  const sakuraCount = Math.min(Math.floor(width / 30), 50);
  const sakuras = [];
  for (let i = 0; i < sakuraCount; i++) {
    const s = new Sakura();
    s.y = Math.random() * height;
    sakuras.push(s);
  }

  // 动画循环
  function animate() {
    ctx.clearRect(0, 0, width, height);
    sakuras.forEach(s => {
      s.update();
      s.draw();
    });
    requestAnimationFrame(animate);
  }

  animate();
})();
