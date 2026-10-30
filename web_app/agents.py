import os
import json
import time
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

load_dotenv()

API_KEY = os.getenv("NUGEN_API_KEY", "").strip()
NUGEN_URL = os.getenv("NUGEN_BASE_URL", "https://api.nugen.in").rstrip("/")

MODEL_SUPPORT = "model_01m61gc299z19jd4"
MODEL_RESEARCH = "model_01m61pt5v52a9jee"

checkpointer = MemorySaver()
agents_cache = {}

def get_agent_specs():
    return [
        {
            "id": "support",
            "name": "Customer Support Agent",
            "role": "ShopEase Operations & Policy Specialist",
            "model_id": MODEL_SUPPORT,
            "domain": "E-Commerce Customer Support, Returns & Escalations",
            "badge": "ShopEase Fine-Tuned"
        },
        {
            "id": "research",
            "name": "Research Paper Agent",
            "role": "Academic AI Literature Specialist",
            "model_id": MODEL_RESEARCH,
            "domain": "Deep Learning, Transformer Architectures & PEFT",
            "badge": "200 AI Papers Fine-Tuned"
        }
    ]

def get_queries(agent_type: str = "support"):
    if agent_type == "research":
        return [
            "Explain how LoRA introduces low-rank decomposition matrices.",
            "What is the mathematical formulation of scaled dot-product attention in Transformers?",
            "How does QLoRA achieve 4-bit quantization without losing perplexity?",
            "Compare FlashAttention memory complexity with standard self-attention."
        ]
    q_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ecommerce_queries.json")
    if os.path.exists(q_path):
        with open(q_path, "r", encoding="utf-8") as f:
            return json.load(f)[:10]
    return [
        "What is the ShopEase return policy for opened electronics?",
        "Explain the step-by-step Tier-2 escalation hierarchy for counterfeit claims.",
        "What are the delivery SLA requirements for lost shipments in transit?",
        "Can a customer stack promotional coupons with loyalty reward points?"
    ]

def build_support_agent():
    prompt = (
        "You are the official ShopEase Customer Support Operations Agent fine-tuned on marketplace policies, "
        "returns, refunds, seller SLAs, counterfeit claims, and escalation hierarchies. "
        "Provide polite, concise, step-by-step resolution according to official ShopEase operations procedures."
    )
    llm = ChatOpenAI(
        base_url=f"{NUGEN_URL}/api/v3/inference",
        api_key=API_KEY,
        model=MODEL_SUPPORT,
        temperature=0.3
    )
    return create_react_agent(
        model=llm,
        tools=[],
        prompt=prompt,
        checkpointer=checkpointer
    )

def build_research_agent():
    prompt = (
        "You are an expert academic AI Research Agent fine-tuned on foundational and landmark machine learning research papers. "
        "Provide thorough, precise, citation-grounded answers about model architectures, attention mechanisms, "
        "PEFT methods like LoRA/QLoRA, and mathematical formulations."
    )
    llm = ChatOpenAI(
        base_url=f"{NUGEN_URL}/api/v3/inference",
        api_key=API_KEY,
        model=MODEL_RESEARCH,
        temperature=0.3
    )
    return create_react_agent(
        model=llm,
        tools=[],
        prompt=prompt,
        checkpointer=checkpointer
    )

def get_agent(agent_type: str):
    if agent_type not in agents_cache:
        agents_cache[agent_type] = build_research_agent() if agent_type == "research" else build_support_agent()
    return agents_cache[agent_type]

def run_agent_turn(agent_type: str, raw_messages: list, session_id: str):
    model_id = MODEL_RESEARCH if agent_type == "research" else MODEL_SUPPORT
    t0 = time.time()
    try:
        agent = get_agent(agent_type)
        langchain_messages = []
        for m in raw_messages:
            role = m.get("role")
            content = m.get("content", "")
            if role == "user":
                langchain_messages.append(HumanMessage(content=content))
            elif role == "assistant":
                langchain_messages.append(AIMessage(content=content))
            elif role == "system":
                langchain_messages.append(SystemMessage(content=content))

        thread_id = f"{session_id}_{agent_type}"
        config = {"configurable": {"thread_id": thread_id}}
        
        result = agent.invoke({"messages": langchain_messages}, config=config)
        output_messages = result.get("messages", [])
        response_text = output_messages[-1].content if output_messages else ""
        
        return {
            "response": response_text,
            "agent_type": agent_type,
            "model_id": model_id,
            "latency_seconds": round(time.time() - t0, 2),
            "thread_id": thread_id
        }
    except Exception as e:
        err_msg = str(e)
        if "429" in err_msg or "Quota limit" in err_msg:
            return {
                "response": "Nugen API Quota limit reached (HTTP 429). Please top up your Nugen credits to continue querying the fine-tuned model.",
                "agent_type": agent_type,
                "model_id": model_id,
                "latency_seconds": round(time.time() - t0, 2),
                "error": "Quota limit reached"
            }
        return {
            "response": f"Error: {err_msg}",
            "agent_type": agent_type,
            "model_id": model_id,
            "latency_seconds": round(time.time() - t0, 2),
            "error": err_msg
        }
