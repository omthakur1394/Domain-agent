import os
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv

from agents import run_agent_turn, get_agent_specs, get_queries

load_dotenv()

app = FastAPI()

class ChatPayload(BaseModel):
    agent_type: str = "support"
    messages: List[dict]
    session_id: Optional[str] = "default"

@app.get("/api/agents")
def list_agents():
    return {"agents": get_agent_specs()}

@app.get("/api/queries")
def list_queries(agent_type: str = "support"):
    return {"queries": get_queries(agent_type)}

@app.post("/api/chat")
def chat(payload: ChatPayload):
    return run_agent_turn(payload.agent_type, payload.messages, payload.session_id)

app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")), name="static")

@app.get("/")
def home():
    return FileResponse(os.path.join(os.path.dirname(__file__), "static", "index.html"))

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=int(os.getenv("PORT", 8000)))
