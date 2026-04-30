# Multi-Agent Crypto Analysis System

Интеллектуальная мультиагентная система для анализа криптовалютных рынков. Принимает аналитические запросы на естественном языке, получает актуальные рыночные данные через внешние API и генерирует структурированные ответы с помощью языковых моделей.

---

## Содержание

- [Возможности](#возможности)
- [Архитектура](#архитектура)
- [Структура проекта](#структура-проекта)
- [Установка](#установка)
- [Конфигурация](#конфигурация)
- [Запуск](#запуск)
- [API](#api)
- [Технологии](#технологии)

---

## Возможности

- Обработка аналитических запросов на естественном языке
- Получение актуальных цен, исторических данных и топ-монет
- Поддержка нескольких провайдеров данных с резервным переключением (CoinGecko, CoinMarketCap)
- Поддержка нескольких LLM-провайдеров (Groq, Gemini)
- Кэширование рыночных данных для снижения нагрузки на API
- REST API на FastAPI
- Веб-интерфейс с поддержкой автодополнения, чата и аналитики

---

## Архитектура

Система построена по мультиагентному принципу. Каждый агент отвечает за строго определённую зону ответственности.

```
Запрос пользователя
        │
        ▼
 ControllerAgent          ← координирует весь пайплайн
        │
   ┌────┴─────┐
   ▼          ▼
PlannerAgent  FetcherAgent
(определяет  (получает данные
 функции и    из CoinGecko /
 параметры)   CoinMarketCap)
        │
        ▼
  DataFormatter           ← подготавливает контекст для LLM
        │
        ▼
 RAGReasonerAgent         ← генерирует финальный ответ через LLM
        │
        ▼
   Ответ пользователю
```

### Агенты

| Агент | Файл | Назначение |
|---|---|---|
| `ControllerAgent` | `controller_agent.py` | Координирует пайплайн выполнения |
| `PlannerAgent` | `planner_agent.py` | Анализирует запрос и определяет нужные функции |
| `FetcherAgent` | `fetcher_agent.py` | Получает данные из внешних API |
| `DataFormatter` | `data_formatter.py` | Форматирует данные в контекст для LLM |
| `RAGReasonerAgent` | `rag_agent.py` | Генерирует аналитический ответ |

---

## Структура проекта

```
multi-agent-system/
├── backend/
│   ├── agent/                      # Мультиагентная система
│   │   ├── contracts/              # Контракты взаимодействия агентов
│   │   │   ├── constants.py
│   │   │   ├── context.py
│   │   │   ├── data.py
│   │   │   ├── enums.py
│   │   │   ├── plan.py
│   │   │   └── trace.py
│   │   ├── providers/              # Адаптеры провайдеров данных
│   │   │   ├── base_provider.py
│   │   │   ├── coingecko_provider.py
│   │   │   ├── coinmarketcap_provider.py
│   │   │   └── provider_manager.py
│   │   ├── base_agent.py
│   │   ├── controller_agent.py
│   │   ├── data_formatter.py
│   │   ├── fetcher_agent.py
│   │   ├── planner_agent.py
│   │   └── rag_agent.py
│   ├── api/
│   │   ├── models/                 # Pydantic-модели запросов и ответов
│   │   │   ├── ask.py
│   │   │   ├── market.py
│   │   │   ├── suggest.py
│   │   │   └── system.py
│   │   ├── routes/                 # Маршруты FastAPI
│   │   │   ├── ask.py
│   │   │   ├── market.py
│   │   │   ├── suggest.py
│   │   │   └── system.py
│   │   └── services/               # Сервисный слой
│   ├── llm/                        # Адаптеры языковых моделей
│   ├── app.py
│   ├── look_and_feel.py
│   ├── main.py                     # Точка входа приложения
│   └── settings.py                 # Конфигурация
├── frontend/
│   ├── css/
│   │   ├── analytics.css
│   │   ├── autocomplete.css
│   │   ├── chat.css
│   │   ├── navbar.css
│   │   └── workflow.css
│   ├── html/
│   │   ├── analytics.html
│   │   ├── chat.html
│   │   ├── navbar.html
│   │   └── workflow.html
│   └── js/
│       ├── dictionary/
│       ├── analytics.js
│       ├── autocomplete.js
│       ├── chat.js
│       ├── common.js
│       ├── global-error.js
│       ├── navbar-loader.js
│       └── workflow.js
├── .env
└── requirements.txt
```

---

## Установка

### Требования

- Python 3.10+
- API-ключи для Groq или Gemini
- API-ключ CoinMarketCap (CoinGecko работает без ключа в бесплатном режиме)

### 1. Клонирование репозитория

```bash
git clone https://github.com/Rilmax04/multi-agent-system.git
cd multi-agent-system
```

### 2. Создание виртуального окружения

```bash
# Linux / macOS
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Установка зависимостей

```bash
pip install -r requirements.txt
```

---

## Конфигурация

Создайте файл `.env` в корне проекта:

```ini
# Языковые модели
GROQ_API_KEY=your_groq_api_key
GEMINI_API_KEY=your_gemini_api_key

# Провайдеры рыночных данных
COINGECKO_API_KEY=your_coingecko_api_key   # опционально
CMC_API_KEY=your_coinmarketcap_api_key     # обязательно для CoinMarketCap
```

> **Примечание:** CoinGecko можно использовать в бесплатном демо-режиме без ключа с лимитом 30 запросов/мин. Для CoinMarketCap ключ обязателен.

### Параметры `settings.py`

```python
agent_models = {
    "planner": {"api": "groq", "model": "llama-4-scout"},
    "reasoner": {"api": "groq", "model": "llama-4-scout"}
}

temperature = 0.1        # Температура генерации (меньше = детерминированнее)
max_tokens = 4096        # Максимальное число токенов в ответе
cache_ttl_prices = 120   # Время жизни кэша цен, секунды
```

---

## Запуск

### Backend

```bash
cd backend
uvicorn main:app --reload
```

Сервер запустится на `http://127.0.0.1:8000`.  
Документация API (Swagger): `http://127.0.0.1:8000/docs`.

### Frontend

```bash
python3 -m http.server 3000 --directory frontend
```
html\chat.html
Интерфейс будет доступен на `http://localhost:3000`.

---

## API

### `POST /ask`

Отправить аналитический вопрос на естественном языке.

**Тело запроса:**
```json
{
  "question": "Какая сейчас цена Bitcoin?"
}
```

**Ответ:**
```json
{
  "answer": "Bitcoin (BTC) торгуется по цене $...",
  "sources": ["coingecko"],
  "trace": [...]
}
```

---

### `GET /market/prices`

Текущие цены монет.

```
GET /market/prices?coins=bitcoin,ethereum
```

---

### `GET /market/history/{coin_id}`

История цены монеты за заданный период.

```
GET /market/history/bitcoin?days=7
```

---

### `GET /market/top`

Топ монет по рыночной капитализации.

```
GET /market/top?limit=10
```

---

### `GET /system/health`

Статус системы и подключённых провайдеров.

---

## Технологии

| Слой | Технологии |
|---|---|
| Backend | Python, FastAPI, Uvicorn |
| Агенты | Кастомная мультиагентная архитектура |
| LLM | Groq (Llama 4), Google Gemini |
| Рыночные данные | CoinGecko API, CoinMarketCap API |
| Frontend | HTML, CSS, Vanilla JavaScript |
| Конфигурация | Pydantic Settings, python-dotenv |

