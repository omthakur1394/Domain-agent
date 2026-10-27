"""
Nugen Intelligence - Automated Model Alignment & Deployment Pipeline

This script automates the full workflow from the Nugen Cookbook:
1. Upload domain document / dataset
2. Generate benchmark questions and answers
3. Create Alignment Project with base model
4. Monitor alignment training progress until READY
5. Deploy the aligned model and poll until DEPLOYED
6. Save deployed model ID for inference
"""

import os
import sys
import time
import json
import argparse
import requests
from dotenv import load_dotenv

# Ensure stdout and stderr handle utf-8 on Windows
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

DOTENV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
if os.path.exists(DOTENV_PATH):
    load_dotenv(dotenv_path=DOTENV_PATH)

API_KEY = os.getenv("NUGEN_API_KEY")
BASE_URL = os.getenv("NUGEN_BASE_URL", "https://api.nugen.in").rstrip("/")

DEFAULT_DOC_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "DATA", "shopease_ecommerce_knowledge_base.txt"
)

def poll_status(url, headers, target_status="READY", interval=10, timeout=1200):
    start_time = time.time()
    while time.time() - start_time < timeout:
        res = requests.get(url, headers=headers)
        if res.status_code != 200:
            print(f"   [Polling] Warning status code {res.status_code}: {res.text}")
            time.sleep(interval)
            continue
        data = res.json()
        status = data.get("status")
        progress = data.get("progress")
        eta = data.get("eta_seconds")
        print(f"   Status: {status} | Progress: {progress} | ETA: {eta}s")

        if status == target_status:
            return data
        if status in ("FAILED", "ERROR"):
            raise RuntimeError(f"Task failed with response: {data}")
        time.sleep(interval)
    raise TimeoutError(f"Polling {url} timed out after {timeout} seconds.")

def main():
    parser = argparse.ArgumentParser(description="Nugen Model Alignment & Deployment Pipeline")
    parser.add_argument("--doc", type=str, default="", help="Path to domain document")
    parser.add_argument("--base-model", type=str, default="", help="Base model ID (e.g. meta-llama/Llama-3.2-3B-Instruct or Qwen/Qwen2.5-0.5B-Instruct)")
    parser.add_argument("--name", type=str, default="", help="Alignment project name")
    parser.add_argument("--auto", action="store_true", help="Run automatically using defaults")
    args = parser.parse_args()

    print("=" * 65)
    print(" 🤖 NUGEN INTELLIGENCE - MODEL ALIGNMENT & DEPLOYMENT PIPELINE")
    print("=" * 65)

    api_key = API_KEY
    if not api_key or api_key == "your_nugen_api_key_here":
        api_key = input("Enter your Nugen API key: ").strip()

    if not api_key:
        print("❌ Error: API key is required.")
        sys.exit(1)

    headers = {
        "Authorization": f"Bearer {api_key}"
    }

    # Step 1: Select document
    doc_path = args.doc
    if not doc_path:
        if args.auto:
            doc_path = DEFAULT_DOC_PATH
        else:
            doc_path = input(f"Enter path to domain document [default: {DEFAULT_DOC_PATH}]: ").strip()
            if not doc_path:
                doc_path = DEFAULT_DOC_PATH

    if not os.path.exists(doc_path):
        print(f"❌ Error: File not found at {doc_path}")
        sys.exit(1)

    # Step 2: Choose Base Model
    base_model = args.base_model
    if not base_model:
        if args.auto:
            base_model = "Qwen/Qwen2.5-0.5B-Instruct"
        else:
            print("\nSelect Base Model for alignment:")
            print("1) Qwen/Qwen2.5-0.5B-Instruct (Fastest, Recommended for first run)")
            print("2) meta-llama/Llama-3.2-3B-Instruct (3B Parameters)")
            print("3) Qwen/Qwen2.5-1.5B-Instruct")
            choice = input("Enter 1, 2, or 3 [default: 1]: ").strip()
            base_model_map = {
                "1": "Qwen/Qwen2.5-0.5B-Instruct",
                "2": "meta-llama/Llama-3.2-3B-Instruct",
                "3": "Qwen/Qwen2.5-1.5B-Instruct"
            }
            base_model = base_model_map.get(choice, "Qwen/Qwen2.5-0.5B-Instruct")
    print(f"Selected Base Model: {base_model}")

    project_name = args.name
    if not project_name:
        if args.auto:
            project_name = f"Domain Alignment Model {int(time.time())}"
        else:
            project_name = input("Enter a name for this alignment project [default: Domain Alignment Model]: ").strip()
            if not project_name:
                project_name = f"Domain Alignment Model {int(time.time())}"

    # Step 3: Upload Document
    print(f"\n📁 Step 1/5: Uploading document '{os.path.basename(doc_path)}'...")
    upload_url = f"{BASE_URL}/api/v3/documents/create"
    payload = {
        "categories": "text/plain",
        "names": os.path.basename(doc_path)
    }

    with open(doc_path, "rb") as f:
        files = {"files": (os.path.basename(doc_path), f)}
        upload_res = requests.post(upload_url, headers=headers, data=payload, files=files)

    if upload_res.status_code == 409:
        doc_id = upload_res.json().get("detail", {}).get("document_id")
        print(f"   ℹ️ Document already uploaded on Nugen. Reusing ID: {doc_id}")
    elif upload_res.status_code in (200, 201):
        doc_ids = upload_res.json().get("document_ids", [])
        if not doc_ids:
            print(f"❌ Document ID not returned: {upload_res.text}")
            sys.exit(1)
        doc_id = doc_ids[0]
        print(f"   Uploaded Document ID: {doc_id}")
    else:
        print(f"❌ Document upload failed: {upload_res.status_code} - {upload_res.text}")
        sys.exit(1)

    # Step 4: Check Document Status
    print("\n⏳ Polling document processing status...")
    doc_status_url = f"{BASE_URL}/api/v3/documents/{doc_id}/status"
    poll_status(doc_status_url, headers, target_status="READY", interval=5, timeout=180)
    print("✅ Document is READY.")

    # Step 5: Generate Benchmark
    print("\n📝 Step 2/5: Generating Benchmark...")
    benchmark_create_url = f"{BASE_URL}/api/v3/benchmarks/create"
    bench_payload = {
        "document_ids": [doc_id],
        "num_questions": 5
    }
    bench_res = requests.post(benchmark_create_url, json=bench_payload, headers=headers)
    if bench_res.status_code == 409:
        benchmark_id = bench_res.json().get("detail", {}).get("benchmark_id")
        print(f"   ℹ️ Reusing existing Benchmark ID: {benchmark_id}")
    elif bench_res.status_code in (200, 201):
        benchmark_id = bench_res.json().get("benchmark_id")
        print(f"   Benchmark ID: {benchmark_id}")
    else:
        print(f"❌ Benchmark creation failed: {bench_res.status_code} - {bench_res.text}")
        sys.exit(1)

    print("⏳ Polling benchmark generation status...")
    bench_status_url = f"{BASE_URL}/api/v3/benchmarks/{benchmark_id}/status"
    poll_status(bench_status_url, headers, target_status="READY", interval=5, timeout=300)
    print("✅ Benchmark generation is READY.")

    # Step 6: Create Alignment Project
    print(f"\n🚀 Step 3/5: Creating Alignment Project '{project_name}'...")
    alignment_create_url = f"{BASE_URL}/api/v3/alignment-projects/create"
    align_payload = {
        "alignment_name": project_name,
        "base_model_id": base_model,
        "document_ids": [doc_id],
        "workflow_id": f"workflow-{int(time.time())}",
        "benchmark_id": benchmark_id,
        "description": f"Domain alignment project for {project_name}"
    }
    align_res = requests.post(alignment_create_url, json=align_payload, headers=headers)
    if align_res.status_code not in (200, 201):
        print(f"❌ Alignment creation failed: {align_res.status_code} - {align_res.text}")
        sys.exit(1)

    alignment_id = align_res.json().get("alignment_id")
    print(f"   Alignment ID: {alignment_id}")

    print("⏳ Polling alignment training status (this may take a few minutes)...")
    align_status_url = f"{BASE_URL}/api/v3/alignment-projects/{alignment_id}/status"
    poll_status(align_status_url, headers, target_status="READY", interval=10, timeout=1800)
    print("✅ Model Alignment completed successfully!")

    # Step 7: Locate Model ID
    print("\n🔍 Step 4/5: Locating aligned model...")
    list_url = f"{BASE_URL}/api/v3/models/aligned"
    list_res = requests.get(list_url, headers=headers)
    models = list_res.json().get("domain_aligned_models", [])

    matched_model = None
    for m in models:
        if m.get("alignment_id") == alignment_id:
            matched_model = m
            break

    if not matched_model and models:
        matched_model = models[0]

    if not matched_model:
        print("❌ Could not locate the aligned model ID from the API.")
        sys.exit(1)

    model_id = matched_model.get("model_id")
    print(f"   Target Model ID: {model_id}")

    # Step 8: Deploy Aligned Model
    print(f"\n⚡ Step 5/5: Deploying model {model_id}...")
    deploy_url = f"{BASE_URL}/api/v3/models/{model_id}/deployment"
    deploy_res = requests.post(deploy_url, headers=headers)
    print(f"   Deploy request response: {deploy_res.status_code} - {deploy_res.text}")

    print("⏳ Polling deployment status...")
    deploy_status_url = f"{BASE_URL}/api/v3/models/{model_id}/deployment/status"
    poll_status(deploy_status_url, headers, target_status="DEPLOYED", interval=5, timeout=300)
    print(f"🎉 SUCCESS! Model '{model_id}' is DEPLOYED and ready for inference!")

    # Save to config
    config_data = {
        "MODEL_ID": model_id,
        "MODEL_NAME": project_name,
        "BASE_MODEL": base_model,
        "ALIGNMENT_ID": alignment_id,
        "DEPLOYED_AT": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    with open("deployed_model.json", "w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=2)

    print("\n" + "=" * 65)
    print(f"🎯 YOUR DEPLOYED MODEL ID: {model_id}")
    print("   Saved to 'deployed_model.json'.")
    print("👉 Next Step: Run 'python inference_app.py' to test inference and begin consuming API credits!")
    print("=" * 65)
if __name__ == "__main__":
    main()
