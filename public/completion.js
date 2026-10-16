const completionSection = document.querySelector('.issue-completion');
const mountainScene = completionSection.querySelector('.completion-mountains');
const completionCounts = [...completionSection.querySelectorAll('[data-final-count]')];
const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

function drawMountains() {
  const width = mountainScene.clientWidth + 40;
  const height = 260;
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  const paper = '239,236,229';
  const hash = (n, seed) => {
    const value = Math.sin(n * 127.1 + seed * 311.7) * 43758.5453;
    return value - Math.floor(value);
  };
  const noise = (x, seed) => {
    const n = Math.floor(x);
    const f = x - n;
    const smooth = f * f * (3 - 2 * f);
    return hash(n, seed) * (1 - smooth) + hash(n + 1, seed) * smooth;
  };
  const layers = [
    { base: .19, amp: .11, color: '#d9dad4', seed: 5 },
    { base: .31, amp: .15, color: '#cdcfc8', seed: 12 },
    { base: .44, amp: .15, color: '#bbbeb6', seed: 22 },
    { base: .61, amp: .21, color: '#a6ada3', seed: 35 },
    { base: .78, amp: .14, color: '#949c92', seed: 50 },
  ];
  const planes = [
    { id: 'mountain-far', indices: [0, 1] },
    { id: 'mountain-mid', indices: [2, 3] },
    { id: 'mountain-near', indices: [4] },
  ];

  planes.forEach((plane) => {
    const canvas = document.getElementById(plane.id);
    canvas.width = Math.round(width * dpr);
    canvas.height = Math.round(height * dpr);
    const context = canvas.getContext('2d');
    if (!context) return;
    context.scale(dpr, dpr);
    context.clearRect(0, 0, width, height);

    plane.indices.forEach((index) => {
      const layer = layers[index];
      context.beginPath();
      context.moveTo(-4, height);
      for (let x = -4; x <= width + 4; x += 2) {
        const position = x / width;
        const ridge = noise(position * 5, layer.seed) * .6
          + noise(position * 15, layer.seed + 3) * .25
          + noise(position * 45, layer.seed + 8) * .1
          + noise(position * 135, layer.seed + 11) * .05;
        const valley = Math.sin(Math.max(0, Math.min(1, position)) * Math.PI) * height * .09 * (index > 1 ? 1 : 0);
        context.lineTo(x, height * (layer.base - layer.amp * ridge) + valley);
      }
      context.lineTo(width + 4, height);
      context.closePath();
      context.fillStyle = layer.color;
      context.fill();

      const mist = context.createLinearGradient(0, height * (layer.base + .05), 0, height * (layer.base + .28));
      mist.addColorStop(0, `rgba(${paper},0)`);
      mist.addColorStop(1, `rgba(${paper},.68)`);
      context.fillStyle = mist;
      context.fillRect(0, height * (layer.base + .05), width, height);
    });

    const pixels = context.getImageData(0, 0, canvas.width, canvas.height);
    let random = 918273 + plane.indices[0];
    for (let pixel = 0; pixel < pixels.data.length; pixel += 4) {
      if (!pixels.data[pixel + 3]) continue;
      random = (Math.imul(random, 1664525) + 1013904223) >>> 0;
      const grain = (random / 4294967296 - .5) * 15;
      for (let channel = 0; channel < 3; channel += 1) {
        pixels.data[pixel + channel] = Math.max(0, Math.min(255, pixels.data[pixel + channel] + grain));
      }
    }
    context.putImageData(pixels, 0, 0);
  });
}

drawMountains();
let mountainResizeFrame;
const redrawMountains = () => {
  cancelAnimationFrame(mountainResizeFrame);
  mountainResizeFrame = requestAnimationFrame(drawMountains);
};
if (typeof ResizeObserver === 'function') new ResizeObserver(redrawMountains).observe(mountainScene);
else window.addEventListener('resize', redrawMountains);

let summaryRevealed = false;
function revealSummary() {
  if (summaryRevealed) return;
  summaryRevealed = true;
  completionSection.classList.add('is-revealed');
  if (reducedMotion) return;

  const started = performance.now();
  const duration = 1600;
  function advance(now) {
    const progress = Math.min(1, (now - started) / duration);
    const eased = 1 - Math.pow(1 - progress, 3);
    completionCounts.forEach((count) => {
      count.textContent = String(Math.round(Number(count.dataset.finalCount) * eased));
    });
    if (progress < 1) requestAnimationFrame(advance);
  }
  completionCounts.forEach((count) => { count.textContent = '0'; });
  requestAnimationFrame(advance);
}

if (!reducedMotion) completionSection.classList.add('has-motion');

if ('IntersectionObserver' in window) {
  const summaryObserver = new IntersectionObserver((entries) => {
    if (!entries.some((entry) => entry.isIntersecting)) return;
    revealSummary();
    summaryObserver.disconnect();
  }, { threshold: .25 });
  summaryObserver.observe(completionSection);

  const mountainObserver = new IntersectionObserver((entries) => {
    if (!entries.some((entry) => entry.isIntersecting)) return;
    if (!reducedMotion) completionSection.classList.add('mountains-arriving');
    mountainObserver.disconnect();
  }, { threshold: .25 });
  mountainObserver.observe(mountainScene);
} else {
  revealSummary();
}
