import json
import logging
import re
from typing import List

from llm import create_erag_api
from settings import settings

logger = logging.getLogger(__name__)

_SYSTEM = """Ты подбираешь подсказки-вопросы для чата криптоаналитики.

Как устроен бэкенд (важно):
- Пайплайн: Planner → Fetcher (CoinGecko и/или CoinMarketCap) → форматирование данных → Reasoner отвечает только по полученным числам и рядам.
- Доступные типы данных: актуальная цена, капитализация, объём за 24ч, изменение за 24ч; исторические цены за выбранный период (дни); списки топ-монет.
- НЕТ в данных: новости, халвинги, регуляторика, «общие знания» о рынке, прогнозы без цифр из API, причины движения цены, если их нет в выгрузке.

Задача: предложи РОВНО 3 коротких следующих вопроса пользователю.
Требования:
- Вопросы должны быть такими, на которые ответ можно собрать из CoinGecko/CoinMarketCap в этом приложении: цена/сравнение монет, динамика за период, топ монет, объёмы и изменения за сутки.
- Не предлагай темы про халвинг, новости, законы, сентимент, NFT-рынок в целом, «почему выросло» без опоры на историю цен — такие запросы заканчиваются ответом «недостаточно данных».
- Язык: как у предыдущих вопросов пользователя (русский или английский). Если истории нет — русский.
- Длина каждого вопроса до 120 символов; без нумерации в тексте; формулировки конкретные (какие монеты, какой горизонт в днях при необходимости).

Ответь ТОЛЬКО валидным JSON без пояснений:
{"suggestions":["вопрос1","вопрос2","вопрос3"]}"""

_FALLBACK = [
    "Сравни текущие цены BTC и ETH",
    "Покажи топ-5 криптовалют по капитализации",
    "Как менялась цена Bitcoin за последние 7 дней?",
]


def _extract_json_object(text: str) -> str:
    s = text.strip()
    if s.startswith("```"):
        s = re.sub(r"^```(?:json)?\s*", "", s, flags=re.IGNORECASE)
        s = re.sub(r"\s*```\s*$", "", s)
    return s.strip()


def _parse_suggestions(raw: str) -> List[str]:
    parsed = json.loads(_extract_json_object(raw))
    items = parsed.get("suggestions") if isinstance(parsed, dict) else None
    if not isinstance(items, list):
        return []
    out = [str(x).strip() for x in items if str(x).strip()]
    return out[:3]


def _pad_suggestions(items: List[str]) -> List[str]:
    seen = set()
    result: List[str] = []
    for s in items:
        if s not in seen:
            seen.add(s)
            result.append(s)
        if len(result) >= 3:
            return result[:3]
    for f in _FALLBACK:
        if f not in seen:
            seen.add(f)
            result.append(f)
        if len(result) >= 3:
            break
    return result[:3]


def get_followup_suggestions(past_questions: List[str]) -> List[str]:
    cfg = settings.get_agent_config("planner")
    api = create_erag_api(cfg["api"], cfg["model"])
    block = "\n".join(f"- {q}" for q in past_questions[-15:])
    user_msg = (
        "Предыдущие вопросы пользователя:\n" + block
        if block.strip()
        else "Предыдущие вопросы пользователя:\n(нет — предложи нейтральные стартовые вопросы по рыночным данным)"
    )
    messages = [
        {"role": "system", "content": _SYSTEM},
        {"role": "user", "content": user_msg},
    ]
    raw = api.chat(messages, temperature=0.35, max_tokens=320)
    try:
        parsed = _parse_suggestions(raw)
    except (json.JSONDecodeError, TypeError, ValueError) as e:
        logger.warning("Follow-up suggestions JSON parse failed: %s", e)
        parsed = []
    return _pad_suggestions(parsed)
