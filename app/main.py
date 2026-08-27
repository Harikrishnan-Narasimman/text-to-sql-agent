"""
FastAPI service exposing the text-to-SQL agent.

Run with:
    uvicorn app.main:app --reload

Then:
    curl -X POST http://localhost:8000/ask \
      -H "Content-Type: application/json" \
      -d '{"question": "Which customer has spent the most money?"}'
"""

import os
from fastapi import FastAPI
from pydantic import BaseModel

from .agent import answer_question

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "sample.db")

app = FastAPI(title="Text-to-SQL Query Agent")


class QuestionRequest(BaseModel):
    question: str


class AgentResponse(BaseModel):
    question: str
    answer: str
    sql: str | None
    attempts: int
    success: bool

@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}

@app.post("/ask", response_model=AgentResponse, tags=["Query"])
def ask(request: QuestionRequest):
    result = answer_question(request.question, DB_PATH)
    return AgentResponse(
        question=result.question,
        answer=result.final_answer,
        sql=result.final_sql,
        attempts=result.attempts,
        success=result.success,
    )