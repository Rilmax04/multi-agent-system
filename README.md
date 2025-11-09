# multi-agent-system
# 🧠 Интеллектуальный ассистент для анализа криптовалют

Мультиагентная система для анализа запросов пользователя о криптовалютах.  
Ассистент использует LLM (Gemini / OpenAI) и API криптобирж для генерации аналитических отчетов.

---

## ⚙️ Основные возможности

- Мультиагентная архитектура:
  - **PlannerAgent** — анализирует запрос пользователя, определяет цели.
  - **FetcherAgent** — получает исторические данные из крипто-API.
  - **RAGReasonerAgent** — создает аналитические выводы на основе данных и модели LLM.
  - **ControllerAgent** — управляет взаимодействием между агентами.
- Поддержка моделей: Gemini, OpenAI, Ollama.
- Веб-интерфейс на **Streamlit**.
- Backend на **FastAPI** с REST API `/ask`.



## 1. Клонирование проекта
```bash
git clone https://github.com/Rilmax04/multi-agent-system.git
cd multi-agent-system
```

## 2️ Создание виртуального окружения

```bash
#  Windows PowerShell
python -m venv myvenv
myvenv\Scripts\activate

# Linux / macOS
python3 -m venv myvenv
source myvenv/bin/activate
```
## 3️ Установка зависимостей
```bash
pip install -r requirements.txt
```

## 4.Настройка API-ключей
```bash
# Groq 
$env:GROQ_API_KEY =ваш_ключ_из_Google_AI_Studio

# Gemini API (Google AI)
$env:GEMINI_API_KEY=ваш_ключ_OpenAI

# coinMarket
$env:CMC_API_KEY=ваш_ключ_API
```

## 5.Запуск проекта (2 термина)
- Backend (FastAPI)
```bash
cd backend
uvicorn main:app --reload
```
- Frontend (Streamlit)
```bash
cd frontend
streamlit run streamlit_app.py
```
Интерфейс: http://localhost:8501