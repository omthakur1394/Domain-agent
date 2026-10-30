import os
import sys
import json
import time
import argparse
import requests
from dotenv import load_dotenv

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

DOTENV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
if os.path.exists(DOTENV_PATH):
    load_dotenv(dotenv_path=DOTENV_PATH)

API_KEY = os.getenv("NUGEN_API_KEY", "").strip()
BASE_URL = os.getenv("NUGEN_BASE_URL", "https://api.nugen.in").rstrip("/")

def run_query(model_id, prompt, api_key, max_tokens=1200):
    url = f"{BASE_URL}/api/v3/inference/chat/completions"
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model_id,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.7,
        "stream": False
    }
    try:
        t0 = time.time()
        res = requests.post(url, json=payload, headers=headers, timeout=90)
        dt = time.time() - t0
        if res.status_code == 200:
            data = res.json()
            usage = data.get("usage", {})
            p_tok = usage.get("prompt_tokens", 0)
            c_tok = usage.get("completion_tokens", 0)
            conf = data.get("confidence_score", 0.0)
            return True, p_tok, c_tok, dt, conf
        return False, 0, 0, dt, 0.0
    except Exception:
        return False, 0, 0, 0.0, 0.0

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--batches", type=int, default=6)
    parser.add_argument("--max-tokens", type=int, default=1200)
    parser.add_argument("--model", type=str, default="")
    parser.add_argument("--auto", action="store_true", default=False)
    args = parser.parse_args()

    api_key = API_KEY
    if not api_key:
        sys.exit(1)

    model_id = args.model or os.getenv("NUGEN_MODEL_ID", "")
    if not model_id and os.path.exists("deployed_model.json"):
        try:
            with open("deployed_model.json", "r", encoding="utf-8") as f:
                model_id = json.load(f).get("MODEL_ID", "")
        except Exception:
            pass
    if not model_id:
        model_id = "model_01m5z6c2z8ked8dj"

    q_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ecommerce_queries.json")
    if os.path.exists(q_file):
        with open(q_file, "r", encoding="utf-8") as f:
            queries = json.load(f)
    else:
        queries = [
            "What is the ShopEase return and refund policy for opened electronics?",
            "Explain the step-by-step escalation process for damaged or counterfeit items.",
            "What are the delivery SLA requirements for lost shipments in transit?",
            "Can a customer stack promotional coupons with loyalty reward points?",
            "What are the seller fulfillment guidelines and late shipment penalties?",
            "How can a customer request an order cancellation after shipment dispatch?",
            "What are the return windows and condition requirements for apparel?",
            "Summarize the ShopEase warranty claim process and documentation needed."
        ]

    batches = args.batches
    total_tasks = batches * len(queries)
    success_count = 0
    fail_count = 0
    total_prompt_tok = 0
    total_comp_tok = 0
    total_latency = 0.0
    conf_scores = []
    start_total_time = time.time()

    for b in range(1, batches + 1):
        for q in queries:
            ok, p_tok, c_tok, lat, conf = run_query(model_id, q, api_key)
            if ok:
                success_count += 1
                total_prompt_tok += p_tok
                total_comp_tok += c_tok
                total_latency += lat
                if conf:
                    conf_scores.append(conf)
            else:
                fail_count += 1
            time.sleep(0.2)

    total_time = time.time() - start_total_time
    total_tokens = total_prompt_tok + total_comp_tok
    avg_latency = (total_latency / success_count) if success_count else 0.0
    avg_conf = (sum(conf_scores) / len(conf_scores)) if conf_scores else 0.0
    tps = (total_comp_tok / total_latency) if total_latency > 0 else 0.0

    report = {
        "model_id": model_id,
        "total_queries": total_tasks,
        "success_rate": f"{(success_count/total_tasks)*100:.1f}%",
        "total_tokens": total_tokens,
        "prompt_tokens": total_prompt_tok,
        "completion_tokens": total_comp_tok,
        "avg_latency_seconds": round(avg_latency, 2),
        "avg_confidence": round(avg_conf, 2),
        "throughput_tps": round(tps, 2),
        "total_seconds": round(total_time, 2),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    with open("benchmark_results.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

if __name__ == "__main__":
    main()
