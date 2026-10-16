const popularLanguages = [
  ['English', 'en'],
  ['Mandarin Chinese', 'zh-CN'],
  ['Hindi', 'hi-IN'],
  ['Spanish', 'es-ES'],
  ['Arabic', 'ar'],
  ['French', 'fr-FR'],
  ['Bengali', 'bn-BD'],
  ['Portuguese', 'pt-BR'],
  ['Russian', 'ru-RU'],
  ['Japanese', 'ja-JP'],
];

const otherLanguages = [
  ['Afrikaans', 'af'], ['Albanian', 'sq'], ['Amharic', 'am'],
  ['Armenian', 'hy'], ['Azerbaijani', 'az'], ['Basque', 'eu'],
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
  ['Tamil', 'ta'], ['Telugu', 'te'], ['Thai', 'th'],
  ['Turkish', 'tr'], ['Ukrainian', 'uk'], ['Urdu', 'ur'],
  ['Uzbek', 'uz'], ['Vietnamese', 'vi'], ['Welsh', 'cy'],
].sort((a, b) => a[0].localeCompare(b[0], 'en'));

const picker = document.querySelector('.language-picker');
const trigger = picker.querySelector('.language-trigger');
const menu = picker.querySelector('.language-menu');
const options = picker.querySelector('.language-options');
const issueDate = new Date(Date.UTC(2026, 9, 13, 12));
let currentLanguage = popularLanguages[0];

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

function selectLanguage(language) {
  currentLanguage = language;
  const [name, locale] = language;
  picker.querySelector('.language-name').textContent = name;
  trigger.setAttribute('aria-label', `Change language, ${name}`);
  trigger.title = name;
  document.documentElement.lang = locale;

  const format = (options) => new Intl.DateTimeFormat(locale, { ...options, timeZone: 'UTC' }).format(issueDate);
  document.querySelector('.weekday').textContent = format({ weekday: 'long' });
  const date = document.querySelector('.date-copy time');
  date.textContent = format({ month: locale === 'en' ? 'long' : 'short', day: 'numeric', year: 'numeric' });
  date.dir = 'auto';

  closeMenu();
  trigger.focus();
}

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
