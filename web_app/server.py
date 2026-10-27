"""
ShopEase AI Operations Console - Backend Server
Proxies requests to Nugen Intelligence and serves the frontend.
No hardcoded values: dynamically fetches models and queries.
"""

import os
import sys
import json
import time
import requests

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv

# Locate .env in current or parent directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(BASE_DIR)

for p in [os.path.join(BASE_DIR, ".env"), os.path.join(PARENT_DIR, ".env")]:
    if os.path.exists(p):
        load_dotenv(p)
        break

API_KEY = os.getenv("NUGEN_API_KEY", "").strip()
NUGEN_URL = os.getenv("NUGEN_BASE_URL", "https://api.nugen.in").rstrip("/")

app = FastAPI(title="Domain AI Operations Console")

class ChatRequest(BaseModel):
    model_id: str
    messages: List[dict]
    max_tokens: Optional[int] = 400
    temperature: Optional[float] = 0.7

@app.get("/api/models")
def get_models():
    """Dynamically fetches all deployed models from Nugen API."""
    if not API_KEY:
        raise HTTPException(status_code=500, detail="NUGEN_API_KEY is missing in .env")

    headers = {"Authorization": f"Bearer {API_KEY}", "Accept": "application/json"}
    try:
        res = requests.get(f"{NUGEN_URL}/api/v3/models/aligned", headers=headers, timeout=15)
        if res.status_code == 200:
            data = res.json()
            models = data.get("domain_aligned_models", [])
            # Filter deployed models or return all
            return JSONResponse({"models": models})
        return JSONResponse({"models": [], "error": res.text}, status_code=res.status_code)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/queries")
def get_sample_queries():
    """Loads domain queries from ecommerce_queries.json."""
    q_file = os.path.join(PARENT_DIR, "ecommerce_queries.json")
    if os.path.exists(q_file):
        with open(q_file, "r", encoding="utf-8") as f:
            queries = json.load(f)
            return JSONResponse({"queries": queries[:12]})
    return JSONResponse({"queries": [
        "What is the ShopEase return policy for opened electronics?",
        "Explain the escalation process for damaged or counterfeit items.",
        "What are the delivery SLA requirements for lost shipments in transit?",
        "Can a customer stack promotional coupons with loyalty reward points?"
    ]})

@app.post("/api/chat")
def chat_completion(req: ChatRequest):
    """Executes chat completion on the selected deployed model."""
    if not API_KEY:
        raise HTTPException(status_code=500, detail="NUGEN_API_KEY is missing in .env")

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": req.model_id,
        "messages": req.messages,
        "max_tokens": req.max_tokens,
        "temperature": req.temperature,
        "stream": False
    }

    t0 = time.time()
    try:
        endpoint = f"{NUGEN_URL}/api/v3/inference/chat/completions"
        res = requests.post(endpoint, json=payload, headers=headers, timeout=90)
        dt = time.time() - t0

        if res.status_code == 200:
            data = res.json()
            choice = data.get("choices", [{}])[0]
            msg = choice.get("message", {}).get("content", "")
            usage = data.get("usage", {})
            return JSONResponse({
                "response": msg,
                "usage": usage,
                "latency_seconds": round(dt, 2),
                "confidence": data.get("confidence_score")
            })
        return JSONResponse({"error": res.text}, status_code=res.status_code)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Static Files & UI Root
STATIC_DIR = os.path.join(BASE_DIR, "static")
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
def serve_index():
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return JSONResponse({"message": "Domain AI API is running. UI files loading..."})

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    print(f"Starting Domain AI Server at http://127.0.0.1:{port}")
    uvicorn.run(app, host="127.0.0.1", port=port)
