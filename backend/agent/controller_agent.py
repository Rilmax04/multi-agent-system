import time
import logging
import traceback
from typing import TypedDict, Optional, List, Dict, Any

from langgraph.graph import StateGraph, END

from agent.planner_agent import PlannerAgent
from agent.fetcher_agent import FetcherAgent
from agent.data_formatter import DataFormatter
from agent.rag_agent import RAGReasonerAgent
from agent.contracts import PlanResult, FetchedData, FormattedContext

logger = logging.getLogger(__name__)


class PipelineState(TypedDict):
    user_query: str
    plan: Optional[PlanResult]
    fetched_data: Optional[FetchedData]
    context: Optional[FormattedContext]
    answer: Optional[str]
    trace: List[Dict[str, Any]]
    errors: List[str]
    pipeline_start_time: float
    current_step: str


class ControllerAgent:
    def __init__(self):
        logger.info("Инициализация ControllerAgent (LangGraph)...")
        self.planner = PlannerAgent()
        self.fetcher = FetcherAgent()
        self.formatter = DataFormatter()
        self.reasoner = RAGReasonerAgent()
        self.graph = self._build_graph()
        logger.info("ControllerAgent готов ✓")

    def _build_graph(self):
        g = StateGraph(PipelineState)
        g.add_node("planner", self._node_planner)
        g.add_node("fetcher", self._node_fetcher)
        g.add_node("formatter", self._node_formatter)
        g.add_node("reasoner", self._node_reasoner)
        g.add_node("handle_error", self._node_error)
        g.set_entry_point("planner")

        for src, dst in [("planner", "fetcher"), ("fetcher", "formatter"),
                         ("formatter", "reasoner")]:
            g.add_conditional_edges(src, self._check_errors,
                                    {"continue": dst, "error": "handle_error"})
        g.add_conditional_edges("reasoner", self._check_errors,
                                {"continue": END, "error": "handle_error"})
        g.add_edge("handle_error", END)
        return g.compile()

    def _make_node(self, step_name, func, state):
        logger.info(f"→ {step_name}")
        start = time.time()
        try:
            result = func()
            elapsed = (time.time() - start) * 1000
            logger.info(f"  ✓ {step_name} ({elapsed:.0f}мс)")
            return {
                "current_step": step_name,
                "trace": state.get("trace", []) + [{
                    "step": step_name, "status": "success", "time_ms": elapsed,
                }],
            }, result
        except Exception as e:
            elapsed = (time.time() - start) * 1000
            logger.error(f"  ✗ {step_name}: {e}")
            return {
                "current_step": step_name,
                "errors": state.get("errors", []) + [f"{step_name}: {e}"],
                "trace": state.get("trace", []) + [{
                    "step": step_name, "status": "error",
                    "time_ms": elapsed, "error": str(e),
                }],
            }, None

    def _node_planner(self, state):
        update, plan = self._make_node("planner",
            lambda: self.planner.execute(state["user_query"]), state)
        if plan: update["plan"] = plan
        return update

    def _node_fetcher(self, state):
        update, data = self._make_node("fetcher",
            lambda: self.fetcher.execute(state["plan"]), state)
        if data: update["fetched_data"] = data
        return update

    def _node_formatter(self, state):
        update, ctx = self._make_node("formatter",
            lambda: self.formatter.format(state["fetched_data"], state["user_query"]), state)
        if ctx: update["context"] = ctx
        return update

    def _node_reasoner(self, state):
        update, answer = self._make_node("reasoner",
            lambda: self.reasoner.execute(state["user_query"], state["context"]), state)
        if answer: update["answer"] = answer
        return update

    def _node_error(self, state):
        errors = state.get("errors", [])
        step = state.get("current_step", "unknown")
        return {"answer": f"Ошибка на этапе '{step}': {'; '.join(errors)}"}

    @staticmethod
    def _check_errors(state):
        return "error" if state.get("errors") else "continue"

    def process_query(self, user_query: str) -> str:
        result = self.get_trace(user_query)
        return result.get("answer", "Ответ не сформирован")

    def get_trace(self, user_query: str) -> dict:
        logger.info(f"{'='*50}\nЗапрос: {user_query}\n{'='*50}")
        initial: PipelineState = {
            "user_query": user_query, "plan": None, "fetched_data": None,
            "context": None, "answer": None, "trace": [], "errors": [],
            "pipeline_start_time": time.time(), "current_step": "start",
        }
        try:
            final = self.graph.invoke(initial)
            total = (time.time() - final["pipeline_start_time"]) * 1000
            self._log_trace(final["trace"], total)
            return {"answer": final.get("answer", ""), "trace": final.get("trace", []),
                    "errors": final.get("errors", []), "total_time_ms": total}
        except Exception as e:
            logger.error(f"Pipeline упал: {traceback.format_exc()}")
            return {"answer": f"Критическая ошибка: {e}", "trace": [], "errors": [str(e)],
                    "total_time_ms": 0}

    @staticmethod
    def _log_trace(trace, total):
        parts = [f"{'✓' if s['status']=='success' else '✗'} {s['step']}({s['time_ms']:.0f}мс)"
                 for s in trace]
        logger.info(f"Pipeline: {' → '.join(parts)} | Итого: {total:.0f}мс")