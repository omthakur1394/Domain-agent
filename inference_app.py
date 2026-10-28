"""
Nugen Intelligence - Silent Benchmark & Credit Consumption Runner
Runs queries quietly in the background and prints only the final benchmark report.
"""

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
    parser = argparse.ArgumentParser(description="Silent Benchmark & Credit Runner")
    parser.add_argument("--batches", type=int, default=6, help="Number of batches to run")
    parser.add_argument("--max-tokens", type=int, default=1200, help="Max tokens per completion")
    parser.add_argument("--model", type=str, default="", help="Model ID override")
    parser.add_argument("--auto", action="store_true", default=False, help="Run non-interactively")
    args = parser.parse_args()

    api_key = API_KEY
    if not api_key:
        if args.auto:
            sys.exit("❌ Error: NUGEN_API_KEY is missing in .env")
        api_key = input("Enter your Nugen API key: ").strip()
    if not api_key:
        sys.exit("❌ Error: API key is required.")

    model_id = args.model or os.getenv("NUGEN_MODEL_ID", "")
    if not model_id and os.path.exists("deployed_model.json"):
        try:
            with open("deployed_model.json", "r", encoding="utf-8") as f:
                model_id = json.load(f).get("MODEL_ID", "")
        except Exception:
            pass
    if not model_id:
        model_id = "model_01m5z6c2z8ked8dj"  # Llama-3.2-3B fallback
    if not args.auto and not args.model and not os.path.exists("deployed_model.json"):
        inp = input(f"Enter DEPLOYED Model ID [default: {model_id}]: ").strip()
        if inp:
            model_id = inp

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

    print("=" * 65)
    print(f" 🎯 ACTIVE ALIGNED MODEL: {model_id} (Llama-3.2-3B)")
    print(f" 🚀 HIGH-COMPUTE CREDIT RUNNER (max_tokens: {args.max_tokens})")
    print("=" * 65)

    if not args.auto and len(sys.argv) == 1:
        batches_str = input(f"Loaded {len(queries)} queries. How many batches to run? [default: {args.batches}]: ").strip()
        batches = int(batches_str) if batches_str.isdigit() else args.batches
    else:
        batches = args.batches

    total_tasks = batches * len(queries)

    print(f"\n⏳ Running {total_tasks} queries across {batches} batches in quiet mode...\n")

    success_count = 0
    fail_count = 0
    total_prompt_tok = 0
    total_comp_tok = 0
    total_latency = 0.0
    conf_scores = []
    start_total_time = time.time()

    task_idx = 0
    for b in range(1, batches + 1):
        for q in queries:
            task_idx += 1
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

            # Print clean milestone updates every 25 queries (no spam)
            if task_idx % 25 == 0 or task_idx == total_tasks:
                pct = int((task_idx / total_tasks) * 100)
                elapsed_sec = int(time.time() - start_total_time)
                elapsed_str = f"{elapsed_sec // 60}m {elapsed_sec % 60}s"
                total_current_tok = total_prompt_tok + total_comp_tok
                print(f"  [Milestone {pct}%] Completed {task_idx}/{total_tasks} queries | Tokens: {total_current_tok:,} | Time: {elapsed_str}")
            time.sleep(0.2)

    total_time = time.time() - start_total_time
    total_tokens = total_prompt_tok + total_comp_tok
    avg_latency = (total_latency / success_count) if success_count else 0.0
    avg_conf = (sum(conf_scores) / len(conf_scores)) if conf_scores else 0.0
    tps = (total_comp_tok / total_latency) if total_latency > 0 else 0.0

    print("\n\n" + "=" * 65)
    print(" 📊 FINAL BENCHMARK & CREDIT CONSUMPTION REPORT")
    print("=" * 65)
    print(f"Aligned Model ID:       {model_id}")
    print(f"Total Queries Executed: {total_tasks}")
    print(f"Successful Requests:    {success_count} / {total_tasks} ({((success_count/total_tasks)*100):.1f}%)")
    print(f"Failed Requests:        {fail_count}")
    print("-" * 65)
    print(f"Prompt Tokens:          {total_prompt_tok:,}")
    print(f"Completion Tokens:      {total_comp_tok:,}")
    print(f"Total Tokens Consumed:  {total_tokens:,}")
    print("-" * 65)
    print(f"Average Response Time:  {avg_latency:.2f} seconds")
    print(f"Generation Throughput:  {tps:.2f} tokens/second")
    if avg_conf:
        print(f"Average Confidence:     {avg_conf:.2f}%")
    print(f"Total Elapsed Time:     {total_time:.2f} seconds ({total_time/60:.2f} minutes)")
    print("=" * 65)

    # Save benchmark summary to disk
    report = {
        "model_id": model_id,
        "total_queries": total_tasks,
        "success_rate": f"{(success_count/total_tasks)*100:.1f}%",
        "total_tokens": total_tokens,
        "prompt_tokens": total_prompt_tok,
        "completion_tokens": total_comp_tok,
        "avg_latency_seconds": round(avg_latency, 2),
        "throughput_tps": round(tps, 2),
        "total_seconds": round(total_time, 2),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    with open("benchmark_results.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("📁 Benchmark results saved to 'benchmark_results.json'.")
    print("👉 Check your updated credit balance at: https://platform.nugen.in\n")

if __name__ == "__main__":
    main()
