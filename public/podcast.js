const headlineData = [
  ['Business', 'Musk’s xAI launches Grok 3 with real-time video understanding', 0],
  ['Tech', 'OpenAI unveils new tools for AI agents', 42],
  ['Markets', 'U.S. stocks rise as AI optimism grows', 78],
  ['AI', 'Google DeepMind previews next-generation model', 123],
  ['World', 'EU moves forward with new AI regulation framework', 168],
  ['Tech', 'Meta announces new AR glasses', 201],
  ['Business', 'Starship takes flight as reusable rocket ambitions grow'],
  ['AI', 'AI’s appetite for compute reshapes the data center'],
  ['Tech', 'Humanoid robots move closer to the factory floor'],
  ['Founders', 'Small teams race to build the next big tools'],
  ['Business', 'The chip race moves beyond the processor'],
  ['AI', 'Agents find a place in everyday work'],
  ['Founders', 'Smaller teams are shipping faster'],
  ['Product', 'A new wave of devices puts AI on the go'],
  ['World', 'Countries redraw the map for advanced chips'],
  ['Tech', 'The browser becomes a workspace for agents'],
  ['Tech', 'The interface after the chat window'],
  ['Tech', 'Search starts to answer the next question'],
  ['Tech', 'Private data becomes useful context'],
  ['Tech', 'Clear controls make complex tools easier to trust'],
  ['Tech', 'Energy moves to the center of the technology story'],
  ['Tech', 'The next interface may not need a screen'],
  ['AI', 'Small models find their place'],
  ['AI', 'AI systems learn when to stop and ask'],
  ['AI', 'The handoff becomes the hard part of AI adoption'],
  ['AI', 'The cost of intelligence becomes a business decision'],
  ['AI', 'Research gets a new set of assistants'],
  ['AI', 'Useful agents bring planning and action together'],
  ['Business', 'Productivity claims get a reality check'],
  ['Business', 'Distribution is still the difficult part'],
  ['Business', 'The workflow becomes the storefront'],
  ['Business', 'Subscriptions must earn a place in the week'],
  ['Business', 'Enterprise adoption starts with a small win'],
  ['Founders', 'The first ten customers still matter most'],
  ['Founders', 'A founder’s underrated skill is editing'],
  ['Founders', 'Small teams change the founder’s job'],
  ['Founders', 'Staying close to users is a quiet advantage'],
  ['Founders', 'A useful routine turns a product into a habit'],
  ['Founders', 'A launch begins the feedback loop'],
  ['Founders', 'Building in public works when it serves users'],
  ['Founders', 'The best early metric might be a conversation'],
  ['Product', 'Voice-first tools ask for a new kind of control'],
  ['Product', 'Better batteries open room for new devices'],
  ['Product', 'Robots move from lab demos to everyday tests'],
  ['Product', 'A focused product can still stand out'],
  ['Product', 'New creative tools make the first draft faster'],
  ['Product', 'The most useful feature may be simplicity'],
  ['World', 'Compute capacity becomes a national priority'],
  ['World', 'Chip rules shape cross-border supply chains'],
  ['World', 'The infrastructure race reaches beyond software'],
];

// When the pipeline built a real episode (feed.podcast) the page plays it; otherwise it shows the built-in sample.
const episode = window.liveFeed && window.liveFeed.podcast;
let duration = episode ? episode.duration_s : 428;
const headlines = episode
  ? episode.chapters.map((chapter) => ({ category: chapter.category, title: chapter.title, start: chapter.start }))
  : headlineData.map(([category, title, start], index) => ({
    category,
    title,
    start: start ?? Math.round(210 + (index - 6) * (213 / 43)),
  }));
const audio = episode ? new Audio() : null;
if (audio) {
  audio.preload = 'none';                                 // nothing is downloaded until someone presses play
  audio.src = episode.audio_url;
}
const escapeText = (value) => String(value).replace(/[&<>"']/g, (character) => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
})[character]);
const formatTime = (seconds) => `${Math.floor(seconds / 60)}:${String(Math.floor(seconds % 60)).padStart(2, '0')}`;
const page = document.querySelector('.podcast-page');
const list = document.querySelector('#headline-list');
const progress = document.querySelector('#player-progress');
const elapsed = document.querySelector('#elapsed-time');
const mainPlay = document.querySelector('#play-main');
const speedButton = document.querySelector('#speed-button');
const speeds = [1, 1.25, 1.5, 2];
let speedIndex = 0;
let playing = false;
let position = episode ? 0 : 42;
let activeHeadline = 0;

function renderHeadlines() {
  list.innerHTML = headlines.map((headline, index) => `
    <li class="headline-row${index === activeHeadline ? ' is-current' : ''}" data-headline="${index}">
      <button class="headline-select" type="button" data-play-headline="${index}" aria-current="${index === activeHeadline}" aria-label="Play from headline ${index + 1}: ${escapeText(headline.title)}">
        <span class="headline-index">${String(index + 1).padStart(2, '0')}</span>
        <span class="headline-rail" aria-hidden="true"></span>
        <span class="headline-category">${escapeText(headline.category)}</span>
        <span class="headline-title">${escapeText(headline.title)}</span>
        <span class="headline-time">${formatTime(headline.start)}</span>
      </button>
    </li>`).join('');
}

function revealCurrentHeadline() {
  const row = list.querySelector(`.headline-row[data-headline="${activeHeadline}"]`);
  if (!row) return;
  const rowBounds = row.getBoundingClientRect();
  const listBounds = list.getBoundingClientRect();
  if (rowBounds.top < listBounds.top || rowBounds.bottom > listBounds.bottom) {
    list.scrollBy({ top: rowBounds.top - listBounds.top - (list.clientHeight - row.offsetHeight) / 2, behavior: 'smooth' });
  }
}

function setPosition(seconds, updateHeadline = true) {
  position = Math.max(0, Math.min(duration, seconds));
  progress.value = Math.floor(position);
  progress.style.setProperty('--played', `${position / duration * 100}%`);
  elapsed.textContent = formatTime(position);
  if (!updateHeadline) return;
  const previousHeadline = activeHeadline;
  activeHeadline = headlines.reduce((selected, headline, index) => headline.start <= position ? index : selected, 0);
  list.querySelectorAll('.headline-row').forEach((row) => {
    const isCurrent = Number(row.dataset.headline) === activeHeadline;
    row.classList.toggle('is-current', isCurrent);
    row.querySelector('.headline-select').setAttribute('aria-current', String(isCurrent));
  });
  if (playing && activeHeadline !== previousHeadline) revealCurrentHeadline();
}

function setPlaying(value) {
  playing = value;
  page.classList.toggle('is-playing', playing);
  mainPlay.setAttribute('aria-label', playing ? 'Pause daily brief' : 'Play daily brief');
}

for (const [index, wave] of [...document.querySelectorAll('.waveform')].entries()) {
  const heights = index === 0 ? [8, 14, 21, 12, 28, 36, 17, 25, 13, 32, 19, 11, 24, 15, 7] : [7, 13, 20, 11, 25, 16, 9];
  wave.innerHTML = heights.map((height) => `<span style="--bar-height:${height}px"></span>`).join('');
}

async function applyHeadlineLanguage(locale) {
  const tr = episode && locale !== 'en' ? await window.loadTranslations(locale) : null;
  headlines.forEach((headline, index) => {
    headline.original = headline.original || headline.title;
    const chapter = episode && episode.chapters[index];
    headline.title = tr && chapter && tr[chapter.id] ? tr[chapter.id].headline : headline.original;
  });
  renderHeadlines();
  setPosition(position);
  const note = document.querySelector('.lineup-kicker span:last-child');
  note.textContent = locale === 'en' || !episode ? `${headlines.length} headlines` : `${headlines.length} · ${window.t('pod.audio')}`;
}
document.addEventListener('bought:language', (event) => applyHeadlineLanguage(event.detail.locale));

renderHeadlines();
if (episode) {                                            // real numbers instead of the sample's
  const minutes = Math.max(1, Math.round(duration / 60));
  document.querySelector('.brief-subtitle').textContent = `${headlines.length} headlines in ${minutes} min`;
  document.querySelector('.player-times time:last-child').textContent = formatTime(duration);
  const facts = document.querySelectorAll('.brief-facts strong');
  facts[0].textContent = headlines.length;
  facts[1].textContent = `${minutes} min`;
  document.querySelector('.lineup-kicker span:last-child').textContent = `${headlines.length} headlines`;
  list.setAttribute('aria-label', `Scroll through all ${headlines.length} headlines`);
  progress.max = Math.floor(duration);
}
setPosition(position);
window.applyUiText();
if (window.boughtLanguage && window.boughtLanguage.locale !== 'en') applyHeadlineLanguage(window.boughtLanguage.locale);

function seekTo(seconds) {
  const target = Math.max(0, Math.min(duration, seconds));
  if (audio) audio.currentTime = target; else setPosition(target);
}

mainPlay.addEventListener('click', () => {
  if (audio) {
    if (audio.paused || audio.ended) {
      if (audio.ended) audio.currentTime = 0;
      audio.play().catch(() => setPlaying(false));
    } else audio.pause();
    return;
  }
  if (position >= duration) setPosition(0);
  setPlaying(!playing);
});
document.querySelectorAll('[data-skip]').forEach((button) => {
  button.addEventListener('click', () => seekTo(position + Number(button.dataset.skip)));
});
progress.addEventListener('input', () => seekTo(Number(progress.value)));
speedButton.addEventListener('click', () => {
  speedIndex = (speedIndex + 1) % speeds.length;
  const speed = speeds[speedIndex];
  if (audio) audio.playbackRate = speed;
  speedButton.textContent = `${speed}×`;
  speedButton.setAttribute('aria-label', `Playback speed, ${speed} times`);
});
list.addEventListener('click', (event) => {
  const button = event.target.closest('[data-play-headline]');
  if (!button) return;
  const headline = Number(button.dataset.playHeadline);
  seekTo(headlines[headline].start);
  if (audio) audio.play().catch(() => setPlaying(false)); else setPlaying(true);
});

if (audio) {
  audio.addEventListener('timeupdate', () => setPosition(audio.currentTime));
  audio.addEventListener('play', () => setPlaying(true));
  audio.addEventListener('pause', () => setPlaying(false));
  audio.addEventListener('ended', () => setPlaying(false));
  if ('mediaSession' in navigator) {                      // lock screen / headphone buttons
    navigator.mediaSession.metadata = new MediaMetadata({ title: 'Today’s Bought Brief', artist: 'Bought.', album: 'The daily brief' });
    const step = (delta) => () => seekTo(audio.currentTime + delta);
    const chapter = (delta) => () => {
      const next = Math.max(0, Math.min(headlines.length - 1, activeHeadline + delta));
      seekTo(headlines[next].start);
    };
    for (const [action, handler] of [['play', () => audio.play()], ['pause', () => audio.pause()], ['seekbackward', step(-15)],
      ['seekforward', step(15)], ['previoustrack', chapter(-1)], ['nexttrack', chapter(1)]]) {
      try { navigator.mediaSession.setActionHandler(action, handler); } catch (e) { /* unsupported action */ }
    }
  }
}

setInterval(() => {
  if (audio || !playing) return;
  setPosition(position + .25 * speeds[speedIndex]);
  if (position >= duration) setPlaying(false);
}, 250);
