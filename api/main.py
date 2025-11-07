from api.agent.planner_agent import PlannerAgent
from api.agent.fetcher_agent import FetcherAgent
from api.agent.rag_agent import RAGReasonerAgent



def main():
    # Создаём агентов
    planner = PlannerAgent(llm_model="gemini")
    fetcher = FetcherAgent()
    reasoner = RAGReasonerAgent(llm_model="gemini")

    # Пример пользовательского запроса
    user_query = "Покажи текущие цены Bitcoin и Ethereum"

    print("\n=== ШАГ 1: Анализ запроса ===")
    functions = planner.analyze_query(user_query)
    print(f"🧩 LLM решила вызвать функции: {functions}")

    print("\n=== ШАГ 2: Сбор данных ===")
    fetcher.fetch_data(functions)

    print("\n=== ШАГ 3: Подготовка данных для RAG ===")
    filtered_data = fetcher.format_for_rag(user_query)

    print("\n=== ШАГ 4: Формирование финального ответа ===")
    final_answer = reasoner.generate_answer(user_query, filtered_data)

    print("\n✅ Итоговый ответ пользователю:")
    print(final_answer)


if __name__ == "__main__":
    main()

