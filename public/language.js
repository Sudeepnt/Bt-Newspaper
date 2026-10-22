const popularLanguages = [
  ['English', 'en'],
  ['Mandarin Chinese', 'zh-CN'],
  ['Spanish', 'es-ES'],
  ['French', 'fr-FR'],
  ['Portuguese', 'pt-BR'],
  ['Russian', 'ru-RU'],
  ['Japanese', 'ja-JP'],
  ['Hindi', 'hi-IN'],
  ['Arabic', 'ar'],
];

const otherLanguages = [
  ['Afrikaans', 'af'], ['Albanian', 'sq'], ['Amharic', 'am'],
  ['Armenian', 'hy'], ['Azerbaijani', 'az'], 
  ['Burmese', 'my'], ['Catalan', 'ca'], ['Czech', 'cs'],
  ['Danish', 'da'], ['Dutch', 'nl'], ['Filipino', 'fil'],
  ['Finnish', 'fi'], ['Georgian', 'ka'], ['German', 'de'],
  ['Greek', 'el'], ['Gujarati', 'gu'], ['Hebrew', 'he'],
  ['Hungarian', 'hu'], ['Icelandic', 'is'], ['Indonesian', 'id'],
  ['Italian', 'it'], ['Kannada', 'kn'], ['Korean', 'ko'],
  ['Malay', 'ms'], ['Malayalam', 'ml'], ['Marathi', 'mr'],
  ['Nepali', 'ne'], ['Norwegian', 'nb'], ['Odia', 'or'],
  ['Persian', 'fa'], ['Polish', 'pl'], ['Punjabi', 'pa'],
  ['Romanian', 'ro'], ['Serbian', 'sr'], ['Sinhala', 'si'],
  ['Slovak', 'sk'], ['Swahili', 'sw'], ['Swedish', 'sv'],
  ['Tamil', 'ta'], ['Thai', 'th'],
  ['Turkish', 'tr'], ['Ukrainian', 'uk'], ['Urdu', 'ur'],
  ['Uzbek', 'uz'], ['Vietnamese', 'vi'], ['Welsh', 'cy'],
  ['Asturian', 'ast'], ['Belarusian', 'be'], ['Bosnian', 'bs'], ['Breton', 'br'],
  ['Bulgarian', 'bg'], ['Croatian', 'hr'], ['Estonian', 'et'], ['Frisian', 'fy'],
  ['Galician', 'gl'], ['Irish', 'ga'], ['Latvian', 'lv'], ['Lithuanian', 'lt'],
  ['Luxembourgish', 'lb'], ['Macedonian', 'mk'], ['Occitan', 'oc'],
  ['Scottish Gaelic', 'gd'], ['Slovenian', 'sl'],
].sort((a, b) => a[0].localeCompare(b[0], 'en'));

const picker = document.querySelector('.language-picker');
const trigger = picker.querySelector('.language-trigger');
const menu = picker.querySelector('.language-menu');
const options = picker.querySelector('.language-options');
const issueDate = new Date(Date.UTC(2026, 9, 13, 12));
let currentLanguage = popularLanguages[0];

// The page's own words, for the most used languages (stories come from the pipeline's translations instead).
const uiText = {
  en: { 'nav.newspaper': 'Newspaper', 'nav.podcast': 'Podcast', 'sec.prime': 'The Prime', 'sec.swipe': 'Swipe cards', 'sec.glance': 'World at a glance',
    'done.issue': "Today's issue", 'done.up': 'You are up to date.', 'done.seal': 'Daily issue complete', 'menu.heading': 'Read in your language',
    'pod.eyebrow': 'The daily brief', 'pod.title': 'Today’s Bought Brief', 'pod.lineup': 'Today’s lineup.', 'pod.inbrief': 'In this brief', 'pod.audio': 'Audio in English' },
  'es-ES': { 'nav.newspaper': 'Periódico', 'nav.podcast': 'Pódcast', 'sec.prime': 'Lo principal', 'sec.swipe': 'Tarjetas', 'sec.glance': 'El mundo de un vistazo',
    'done.issue': 'Edición de hoy', 'done.up': 'Estás al día.', 'done.seal': 'Edición diaria completa', 'menu.heading': 'Lee en tu idioma',
    'pod.eyebrow': 'El resumen diario', 'pod.title': 'El resumen de Bought de hoy', 'pod.lineup': 'Los titulares de hoy.', 'pod.inbrief': 'En este resumen', 'pod.audio': 'Audio en inglés' },
  'fr-FR': { 'nav.newspaper': 'Journal', 'nav.podcast': 'Podcast', 'sec.prime': 'À la une', 'sec.swipe': 'Cartes à glisser', 'sec.glance': 'Le monde en un coup d’œil',
    'done.issue': 'Édition du jour', 'done.up': 'Vous êtes à jour.', 'done.seal': 'Édition du jour complète', 'menu.heading': 'Lisez dans votre langue',
    'pod.eyebrow': 'Le résumé quotidien', 'pod.title': 'Le résumé Bought du jour', 'pod.lineup': 'Les titres du jour.', 'pod.inbrief': 'Dans ce résumé', 'pod.audio': 'Audio en anglais' },
  'pt-BR': { 'nav.newspaper': 'Jornal', 'nav.podcast': 'Podcast', 'sec.prime': 'Destaques', 'sec.swipe': 'Cartões', 'sec.glance': 'O mundo em resumo',
    'done.issue': 'Edição de hoje', 'done.up': 'Você está em dia.', 'done.seal': 'Edição diária completa', 'menu.heading': 'Leia no seu idioma',
    'pod.eyebrow': 'O resumo diário', 'pod.title': 'O resumo Bought de hoje', 'pod.lineup': 'As manchetes de hoje.', 'pod.inbrief': 'Neste resumo', 'pod.audio': 'Áudio em inglês' },
  'hi-IN': { 'nav.newspaper': 'अखबार', 'nav.podcast': 'पॉडकास्ट', 'sec.prime': 'मुख्य खबरें', 'sec.swipe': 'स्वाइप कार्ड', 'sec.glance': 'एक नज़र में दुनिया',
    'done.issue': 'आज का अंक', 'done.up': 'आप अपडेट हैं।', 'done.seal': 'दैनिक अंक पूरा हुआ', 'menu.heading': 'अपनी भाषा में पढ़ें',
    'pod.eyebrow': 'दैनिक ब्रीफ़', 'pod.title': 'आज का Bought ब्रीफ़', 'pod.lineup': 'आज की सुर्खियाँ।', 'pod.inbrief': 'इस ब्रीफ़ में', 'pod.audio': 'ऑडियो अंग्रेज़ी में' },
  'zh-CN': { 'nav.newspaper': '报纸', 'nav.podcast': '播客', 'sec.prime': '头条', 'sec.swipe': '滑动卡片', 'sec.glance': '一览天下',
    'done.issue': '今日刊', 'done.up': '您已阅读完毕。', 'done.seal': '今日刊已读完', 'menu.heading': '用您的语言阅读',
    'pod.eyebrow': '每日简报', 'pod.title': '今日 Bought 简报', 'pod.lineup': '今日要闻。', 'pod.inbrief': '本期内容', 'pod.audio': '音频为英语' },
  ar: { 'nav.newspaper': 'الصحيفة', 'nav.podcast': 'بودكاست', 'sec.prime': 'الأبرز', 'sec.swipe': 'بطاقات التمرير', 'sec.glance': 'العالم بنظرة سريعة',
    'done.issue': 'عدد اليوم', 'done.up': 'أنت على اطلاع كامل.', 'done.seal': 'اكتمل عدد اليوم', 'menu.heading': 'اقرأ بلغتك',
    'pod.eyebrow': 'الموجز اليومي', 'pod.title': 'موجز Bought اليوم', 'pod.lineup': 'عناوين اليوم.', 'pod.inbrief': 'في هذا الموجز', 'pod.audio': 'الصوت بالإنجليزية' },
  'ru-RU': { 'nav.newspaper': 'Газета', 'nav.podcast': 'Подкаст', 'sec.prime': 'Главное', 'sec.swipe': 'Карточки', 'sec.glance': 'Мир вкратце',
    'done.issue': 'Выпуск сегодня', 'done.up': 'Вы в курсе всех новостей.', 'done.seal': 'Ежедневный выпуск завершён', 'menu.heading': 'Читайте на своём языке',
    'pod.eyebrow': 'Ежедневный брифинг', 'pod.title': 'Брифинг Bought на сегодня', 'pod.lineup': 'Заголовки дня.', 'pod.inbrief': 'В этом брифинге', 'pod.audio': 'Аудио на английском' },
  'ja-JP': { 'nav.newspaper': '新聞', 'nav.podcast': 'ポッドキャスト', 'sec.prime': 'トップ記事', 'sec.swipe': 'スワイプカード', 'sec.glance': '世界のいま',
    'done.issue': '今日の号', 'done.up': 'すべて読み終えました。', 'done.seal': '本日の号は完了', 'menu.heading': 'あなたの言語で読む',
    'pod.eyebrow': 'デイリーブリーフ', 'pod.title': '今日のBoughtブリーフ', 'pod.lineup': '今日のヘッドライン。', 'pod.inbrief': 'このブリーフの内容', 'pod.audio': '音声は英語です' },
};
const rtlLocales = ['ar', 'he', 'fa', 'ur'];
const storageKey = 'bought.language';
const translationCache = {};

// Pages call these: t(key) for the page's words, applyUiText() after they add elements, loadTranslations(locale) for stories.
window.t = (key) => (uiText[currentLanguage[1]] && uiText[currentLanguage[1]][key]) || uiText.en[key] || key;
window.applyUiText = () => {
  document.querySelectorAll('[data-i18n]').forEach((el) => { el.textContent = window.t(el.dataset.i18n); });
};
window.loadTranslations = async (locale) => {
  if (locale === 'en') return null;
  if (!(locale in translationCache)) {
    translationCache[locale] = fetch(`live/translations/${locale}.json`, { cache: 'no-cache' })
      .then((res) => (res.ok ? res.json() : null)).catch(() => null);
  }
  return translationCache[locale];
};

function renderGroup(label, languages) {
  const group = document.createElement('section');
  group.className = 'language-group';
  const heading = document.createElement('h2');
  heading.textContent = label;
  group.append(heading);

  for (const language of languages) {
    const [name, locale] = language;
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'language-option';
    button.textContent = name;
    button.setAttribute('aria-current', locale === currentLanguage[1] ? 'true' : 'false');
    button.addEventListener('click', () => selectLanguage(language));
    group.append(button);
  }

  options.append(group);
}

function renderOptions() {
  options.replaceChildren();
  renderGroup('Most used', popularLanguages);
  renderGroup('More languages · A–Z', otherLanguages);
}

function closeMenu() {
  menu.hidden = true;
  trigger.setAttribute('aria-expanded', 'false');
}

function selectLanguage(language, { silent = false } = {}) {
  currentLanguage = language;
  const [name, locale] = language;
  window.boughtLanguage = { name, locale };
  try { localStorage.setItem(storageKey, locale); } catch (e) { /* private mode: the choice just isn't remembered */ }
  document.documentElement.dir = rtlLocales.includes(locale.split('-')[0]) ? 'rtl' : 'ltr';
  picker.querySelector('.language-name').textContent = name;
  trigger.setAttribute('aria-label', `Change language, ${name}`);
  trigger.title = name;
  document.documentElement.lang = locale;

  const format = (options) => new Intl.DateTimeFormat(locale, { ...options, timeZone: 'UTC' }).format(issueDate);
  document.querySelector('.weekday').textContent = format({ weekday: 'long' });
  const date = document.querySelector('.date-copy time');
  date.textContent = format({ month: locale === 'en' ? 'long' : 'short', day: 'numeric', year: 'numeric' });
  date.dir = 'auto';

  window.applyUiText();
  document.dispatchEvent(new CustomEvent('bought:language', { detail: { name, locale } }));
  if (silent) return;
  closeMenu();
  trigger.focus();
}

// Remember the choice across pages and visits.
window.boughtLanguage = { name: currentLanguage[0], locale: currentLanguage[1] };
try {
  const saved = localStorage.getItem(storageKey);
  const language = [...popularLanguages, ...otherLanguages].find(([, locale]) => locale === saved);
  if (language && saved !== 'en') selectLanguage(language, { silent: true });
} catch (e) { /* storage blocked: stay in English */ }

trigger.addEventListener('click', () => {
  const opening = menu.hidden;
  menu.hidden = !opening;
  trigger.setAttribute('aria-expanded', String(opening));
  if (opening) {
    renderOptions();
  }
});
document.addEventListener('pointerdown', (event) => {
  if (!picker.contains(event.target)) closeMenu();
});
document.addEventListener('keydown', (event) => {
  if (event.key === 'Escape' && !menu.hidden) {
    closeMenu();
    trigger.focus();
  }
});
