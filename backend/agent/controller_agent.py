import traceback
import logging
from agent.planner_agent import PlannerAgent
from agent.fetcher_agent import FetcherAgent
from agent.rag_agent import RAGReasonerAgent
from llm import create_erag_api

# === Настройка логирования ===
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]  # вывод в консоль
)


class ControllerAgent:
    def __init__(self, llm_model="gemini"):
        logging.info("Инициализация ControllerAgent...")
        try:
            self.llm = create_erag_api(api_type="gemini", model="gemini-2.5-flash")
            self.planner = PlannerAgent(llm_model=llm_model)
            self.fetcher = FetcherAgent()
            self.reasoner = RAGReasonerAgent(llm_model=llm_model)

            self.state = {
                "user_query": None,
                "last_action": None,
                "data_store": {},
            }
            logging.info("ControllerAgent успешно инициализирован ✅")
        except Exception as e:
            logging.error("Ошибка при инициализации ControllerAgent:")
            logging.error(traceback.format_exc())
            raise e

    def process_query(self, user_query: str):
        logging.info(f"📩 Получен запрос пользователя: {user_query}")
        self.state["user_query"] = user_query
        instruction = "Начни обработку запроса пользователя."

        try:
            while True:
                logging.info(f"🧠 Этап мышления. Инструкция: {instruction}")
                decision = self.think(instruction)
                logging.info(f"🤔 Решение модели: {decision}")

                next_agent = self.parse_next_agent(decision)
                logging.info(f"➡ Следующий агент: {next_agent}")

                if next_agent == "planner":
                    logging.info("🔍 Запуск PlannerAgent...")
                    plan = self.planner.analyze_query(user_query)
                    logging.info(f"✅ PlannerAgent вернул план: {plan}")
                    self.state["data_store"]["planner"] = plan
                    self.state["last_action"] = "analyzed_query"
                    instruction = "PlannerAgent завершил анализ. Что делать дальше?"

                elif next_agent == "fetcher":
                    logging.info("📡 Запуск FetcherAgent...")
                    plan = self.state["data_store"].get("planner", {})
                    period = self.extract_period(user_query)
                    logging.info(f"⏱ Определён период: {period} дней")
                    data = self.fetcher.fetch_data(plan, days=period)
                    logging.info(f"✅ FetcherAgent получил данные: {len(data) if data else 'пусто'} записей")
                    self.state["data_store"]["fetcher"] = data
                    self.state["last_action"] = "fetched_data"
                    instruction = "FetcherAgent собрал данные. Что делать дальше?"

                elif next_agent == "reasoner":
                    logging.info("🧩 Запуск RAGReasonerAgent...")
                    planner_data = self.state["data_store"].get("planner", {})
                    formatted = self.fetcher.format_for_rag(
                        user_query=user_query,
                        selected_coins=planner_data.get("coins", []),
                        period_days=self.extract_period(user_query)
                    )
                    answer = self.reasoner.generate_answer(user_query, formatted)
                    logging.info("✅ RAGReasonerAgent сгенерировал ответ.")
                    self.state["data_store"]["final_answer"] = answer
                    self.state["last_action"] = "generated_answer"
                    instruction = "RAGReasonerAgent создал ответ. Заверши процесс."

                elif next_agent == "done":
                    logging.info("🏁 Процесс завершён.")
                    return self.state["data_store"].get("final_answer", "Ответ не сформирован")

                else:
                    logging.warning(f"⚠️ Не удалось определить следующего агента по тексту: {decision}")
                    return self.state["data_store"].get("final_answer", "Ответ не сформирован")

        except Exception as e:
            logging.error("❌ Ошибка при обработке запроса в ControllerAgent:")
            logging.error(traceback.format_exc())
            return f"⚠ Ошибка при обработке: {type(e).__name__}: {e}"

    def think(self, instruction):
        system_prompt = (
            "Ты управляющий агент мультиагентной системы для анализа криптовалют. "
            "Ты решаешь, какой агент должен быть вызван следующим:\n"
            "- PlannerAgent (анализирует запрос, определяет функции и монеты)\n"
            "- FetcherAgent (извлекает данные из API)\n"
            "- RAGReasonerAgent (создаёт итоговый аналитический ответ)\n\n"
            "Отвечай коротко и естественно, например:\n"
            "→ Следующий агент: FetcherAgent.\n"
            "→ Далее нужно вызвать RAGReasonerAgent.\n"
            "→ Работа завершена."
        )

        context = (
            f"Последнее действие: {self.state.get('last_action')}\n"
            f"Известные данные: {list(self.state.get('data_store', {}).keys())}\n"
            f"Инструкция: {instruction}"
        )

        llm_prompt = f"{system_prompt}\n\nКонтекст:\n{context}"

        logging.info("📨 Отправка промпта в LLM...")
        decision = self.llm.chat([{"role": "user", "content": llm_prompt}])
        logging.info(f"📤 Ответ LLM: {decision}")
        return decision

    def parse_next_agent(self, text: str) -> str:
        text = text.lower()
        if "planner" in text:
            return "planner"
        if "fetcher" in text:
            return "fetcher"
        if "reasoner" in text or "rag" in text:
            return "reasoner"
        if "заверши" in text or "готово" in text or "done" in text:
            return "done"
        return ""

    def extract_period(self, text: str) -> int:
        prompt = (
            "Определи, за какой период времени пользователь хочет получить данные о криптовалюте. "
            "Ответь только одним числом — количеством дней.\n\n"
            f"Пример: 'за неделю' → 7, 'за месяц' → 30, 'за квартал' → 90, 'за год' → 365.\n\n"
            f"Запрос пользователя: {text}"
        )

        try:
            response = self.llm.chat([{"role": "user", "content": prompt}])
            logging.info(f"📤 Ответ LLM для периода: {response}")
            period = int(response)
            if period > 0:
                return period
            else:
                logging.warning("⚠️ Неверный период, используется значение по умолчанию = 7")
                return 7
        except Exception as e:
            logging.error("Ошибка при извлечении периода:")
            logging.error(traceback.format_exc())
            return 7
