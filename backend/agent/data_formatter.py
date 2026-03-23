import json
import logging

from agent.contracts import FetchedData, FormattedContext
from settings import settings

logger = logging.getLogger(__name__)


class DataFormatter:
    def format(self, fetched_data: FetchedData, user_query: str = "") -> FormattedContext:
        entries = []
        for entry in fetched_data.entries:
            if entry.data is not None:
                entries.append({"function": entry.function, "data": entry.data})

        if fetched_data.errors:
            entries.append({"data_quality": {
                "completeness": fetched_data.completeness,
                "errors": fetched_data.errors,
            }})

        context_str = json.dumps(entries, ensure_ascii=False, indent=2)
        was_truncated = False

        if len(context_str) > settings.max_context_length:
            logger.warning(f"[Formatter] Контекст {len(context_str)} > {settings.max_context_length}, усечение")
            entries = self._truncate(entries)
            context_str = json.dumps(entries, ensure_ascii=False, indent=2)
            was_truncated = True

        result = FormattedContext(context_str=context_str,
                                 total_chars=len(context_str), was_truncated=was_truncated)
        logger.info(f"[Formatter] {len(entries)} записей, {result.total_chars} символов, усечён={was_truncated}")
        return result

    @staticmethod
    def _truncate(entries):
        truncated = []
        for entry in entries:
            data = entry.get("data")
            if isinstance(data, dict):
                for cid, cd in data.items():
                    if isinstance(cd, dict) and "prices" in cd:
                        prices = cd["prices"]
                        if len(prices) > 10:
                            step = max(1, len(prices) // 10)
                            cd["prices"] = prices[::step]
                            cd["_note"] = f"Сжато с {len(prices)} точек"
            if isinstance(data, list) and len(data) > 5:
                entry["data"] = data[:5]
                entry["_note"] = "Усечено до 5"
            truncated.append(entry)
        return truncated