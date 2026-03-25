const CRYPTO = [
  "Абстракция аккаунта","Автоматический маркет-мейкер","АММ","Авторитетный мастернод",
  "Агрегатор DeFi","Адаптивный шардинг","Адрес","Аирдроп","Алгоритмический стейблкоин",
  "Альткоин","Альфа","Анархо-капитализм","Аномальная доходность","Аппаратный кошелёк",
  "Асинхронный","Атака 51%","Атака флэш-кредита","Атомарный своп",
  "Бейкеры","Биткоин-банкомат","BTM","Биткойнер","Блокировка токенов","Блокчейн",
  "Блокчейн-трайбализм","Валидатор","Взаимозаменяемый","Византийская отказоустойчивость",
  "BFT","Виртуальная машина Ethereum","EVM","Вош-трейдинг","Время блока",
  "Газ","Генезис-блок","Годовая процентная доходность","APY","Годовая процентная ставка","APR",
  "Горячее хранение","Горячий кошелек","Граничные узлы","Групповой майнинг",
  "Двухфакторная аутентификация","2FA","Делегированное доказательство доли","dPOS",
  "Дерево Меркла","Децентрализованная биржа","DEX","Децентрализованное управление",
  "ДАО","DAICO","Децентрализованные приложения","DApps","Децентрализованный",
  "Доказательство мошенничества","Доминирование Биткоина","BTCD",
  "Заголовок блока","Закрытый ключ","Залоговые токены","Защищенный реестр",
  "Извлекаемая майнерами ценность","MEV","Инфляция",
  "Каскадные ликвидации","Кастодиальный кошелёк","Кастодиан","Консенсус",
  "Консорциумный блокчейн","Корпоративный блокчейн","Кривая привязки",
  "Криптовалюта","Криптоджекинг","Криптозима","Криптомиксер",
  "Ликвидация","Ликвидность","Ликвидный стейкинг","Лимит газа","Ложный пробой",
  "Майнеры","Майнинг","Мейннет","Мемкоин","Метавселенная","Механизм консенсуса","Мосты",
  "Неизменность","Непостоянные потери","Нерегулируемый реестр",
  "Обеспеченная долговая позиция","CDP","Облачный майнинг","Обозреватель блоков",
  "Общая заблокированная стоимость","TVL","Объем торгов","Ончейн",
  "Первичное предложение монет","ICO","IDO","Подтверждение",
  "Полностью разводненная стоимость","FDV","Полный узел","Производитель блока",
  "Протокол","Публичный адрес","Распределённый реестр","Рыночная капитализация",
  "Сатоши Накамото","Сид-фраза","Служебный токен","Смарт-контракт",
  "Стейблкоин","Стейкинг","Стоимость газа","Тест Хауи","Тестнет","DLT",
  "Токен управления","Токеномика","Токенсейл","TPS","Узел","Управление",
  "Фиат","Фиатный шлюз","Флиппенинг","Флэш-кредит","Форк","Фронтраннинг",
  "Хардфорк","Хеш","Холодное хранение","Холодный кошелек",
  "Централизованная биржа","CEX","Циркулирующее предложение","CBDC",
  "Шардинг","Шифропанк","Экзит-скам","Эмиссия токенов","Эпоха",
  "Airnode","ASIC","Bagholder","Beacon Chain","BEP-2","BEP-20","BEP-721","BEP-95",
  "Binance Labs","Binance Launchpad","BitLicense","CeDeFi","Coinbase","CPU Miner",
  "DeFi","EEA","ERC-20","ERC-721","ERC-777","ERC-1155","EIP","FOMO",
  "GameFi","Geth","HODL","KYC","Layer 0","Layer 1","Layer 2","NFT",
  "PoA","PoS","PoW","Rug Pull","SegWit"
];

const input = document.getElementById('chatInput');
const list  = document.getElementById('autocompleteList');
let active = -1, matches = [], timer, wikiCtrl;

input.addEventListener('input', () => {
  const val = input.value.split(/\s+/).pop();
  if (val.length < 1) { closeList(); return; }

  const lower  = val.toLowerCase();
  const crypto = CRYPTO.filter(t => t.toLowerCase().startsWith(lower)).slice(0, 6);

  clearTimeout(timer);
  if (wikiCtrl) wikiCtrl.abort();

  render(crypto, [], val);

  if (crypto.length < 6) {
    timer = setTimeout(() => fetchWiki(val, crypto), 350);
  }
});

async function fetchWiki(val, crypto) {
  wikiCtrl = new AbortController();
  try {
    const url = `https://ru.wikipedia.org/w/api.php?action=opensearch&search=${encodeURIComponent(val)}&limit=20&format=json&origin=*`;
    const res  = await fetch(url, { signal: wikiCtrl.signal });
    const data = await res.json();
    const seen = new Set(crypto.map(s => s.toLowerCase()));
    const wiki = data[1]
      .map(s => s.split(/[\s,.(]/)[0])
      .filter(w => w.toLowerCase().startsWith(val.toLowerCase()) && !seen.has(w.toLowerCase()))
      .filter((w, i, a) => a.indexOf(w) === i)
      .slice(0, 8 - crypto.length);
    render(crypto, wiki, val);
  } catch (e) {}
}

function render(crypto, wiki, val) {
  matches = [...crypto, ...wiki];
  active  = -1;
  if (!matches.length) { closeList(); return; }

  list.innerHTML = [
    ...crypto.map((t, i) => item(t, val, i,              'crypto')),
    ...wiki  .map((t, i) => item(t, val, i + crypto.length, 'wiki')),
  ].join('');
  list.className = 'open';
}

function item(t, val, i, type) {
  const lower = val.toLowerCase();
  const idx   = t.toLowerCase().indexOf(lower);
  const hi    = idx >= 0
    ? t.slice(0, idx) + '<mark>' + t.slice(idx, idx + val.length) + '</mark>' + t.slice(idx + val.length)
    : t;
  const badge = type === 'crypto'
    ? '<span class="badge badge-crypto">крипто</span>'
    : '<span class="badge badge-wiki">wiki</span>';
  return `<li data-i="${i}">${badge}${hi}</li>`;
}

function pick(i) {
  const parts = input.value.split(/\s+/);
  parts[parts.length - 1] = matches[i];
  input.value = parts.join(' ') + ' ';
  closeList();
  input.focus();
}

list.addEventListener('mousedown', e => {
  const li = e.target.closest('li');
  if (li) pick(+li.dataset.i);
});

input.addEventListener('keydown', e => {
  if (e.key === 'ArrowDown')  { e.preventDefault(); setActive(active + 1); }
  if (e.key === 'ArrowUp')    { e.preventDefault(); setActive(active - 1); }
  if (e.key === 'Enter' && active >= 0) { e.preventDefault(); pick(active); }
  if (e.key === 'Escape') closeList();
});

function setActive(i) {
  const lis = list.querySelectorAll('li');
  active = Math.max(0, Math.min(i, lis.length - 1));
  lis.forEach((el, j) => el.classList.toggle('active', j === active));
}

function closeList() {
  list.className = '';
  list.innerHTML = '';
  active  = -1;
  matches = [];
}

document.addEventListener('click', e => {
  if (!e.target.closest('.wrap')) closeList();
});