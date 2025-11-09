from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from agent.controller_agent import ControllerAgent

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

controller = ControllerAgent(llm_model="gemini")

class Query(BaseModel):
    question: str

@app.post("/ask")
def ask_model(request: Query):
    try:
        answer = controller.process_query(request.question)
        return {"answer": answer}
    except Exception as e:
        import traceback
        traceback.print_exc()  # выведет полный стек ошибки в консоль
        return {"answer": f"⚠ Ошибка при обработке: {type(e).__name__}: {e}"}
@app.get("/")
def root():
    return {"message": "✅ Backend работает"}
