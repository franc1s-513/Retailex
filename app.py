"""Root FastAPI entry point: serves the frontend and the Retail Copilot API."""

import os
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

try:
    from backend.insights import (
        get_stockout_risks,
        get_dead_stock,
        get_sales_anomalies,
    )
    from backend.llm_agent import RetailCopilotAgent, _load_env
except ImportError:
    from insights import get_stockout_risks, get_dead_stock, get_sales_anomalies
    from llm_agent import RetailCopilotAgent, _load_env

_load_env()

FRONTEND_DIR = Path(__file__).resolve().parent / "frontend" / "dist"

app = FastAPI(title="Retail Copilot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:8000", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


_agent = None


def get_agent() -> RetailCopilotAgent:
    global _agent
    if _agent is None:
        _agent = RetailCopilotAgent()
    return _agent


class ChatRequest(BaseModel):
    message: str


@app.get("/api/morning-briefing")
def morning_briefing() -> dict:
    try:
        return {
            "stockout_risks": get_stockout_risks(),
            "dead_stock": get_dead_stock(),
            "sales_anomalies": get_sales_anomalies(),
        }
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/chat")
def chat(payload: ChatRequest) -> dict:
    message = payload.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    try:
        agent = get_agent()
        result = agent.ask(message)
        if isinstance(result, dict):
            return result
        return {"response": result, "sql": None, "row_count": 0}
    except Exception as exc:
        return {
            "response": f"The copilot encountered an issue: {exc}. Please verify your network connection and try again.",
            "sql": None,
            "row_count": 0,
        }


@app.get("/")
def index() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")


app.mount("/", StaticFiles(directory=FRONTEND_DIR), name="frontend")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)