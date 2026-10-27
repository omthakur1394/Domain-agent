"""
Nugen Intelligence - API Connection & Aligned Models Verifier
"""

import os
import sys
import json
import requests
from dotenv import load_dotenv

# Ensure stdout and stderr handle utf-8 on Windows
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Load environment variables explicitly from local workspace
DOTENV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
if os.path.exists(DOTENV_PATH):
    load_dotenv(dotenv_path=DOTENV_PATH)

API_KEY = os.getenv("NUGEN_API_KEY")
BASE_URL = os.getenv("NUGEN_BASE_URL", "https://api.nugen.in").rstrip("/")

def main():
    print("=" * 60)
    print(" 🚀 NUGEN INTELLIGENCE - CONNECTION & MODELS CHECK")
    print("=" * 60)

    api_key = API_KEY
    if not api_key or api_key == "your_nugen_api_key_here":
        api_key = input("Enter your Nugen API key: ").strip()

    if not api_key:
        print("\n❌ Error: No API key provided.")
        print("Please obtain an API key from https://platform.nugen.in/ (API Keys tab)")
        print("and set it in .env as NUGEN_API_KEY=...\n")
        sys.exit(1)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json"
    }

    print(f"\n1. Testing API Key against {BASE_URL}...")
    try:
        url = f"{BASE_URL}/api/v3/models/aligned"
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            models = data.get("domain_aligned_models", [])
            print("✅ Authentication Successful!\n")
            print(f"📊 Total Domain-Aligned Models Found: {len(models)}")
            print("-" * 60)
            
            if not models:
                print("ℹ️  You have not aligned any models yet.")
                print("👉 Next step: Run 'python align_model.py' to align your first model!")
            else:
                for idx, m in enumerate(models, 1):
                    m_id = m.get("model_id")
                    m_name = m.get("model_name")
                    status = m.get("deployment_status")
                    base = m.get("base_model_id")
                    created = m.get("created_at")
                    print(f"[{idx}] Model ID: {m_id}")
                    print(f"    Name:   {m_name}")
                    print(f"    Base:   {base}")
                    print(f"    Status: {status}")
                    print(f"    Created:{created}\n")

                deployed_models = [m for m in models if m.get("deployment_status") == "DEPLOYED"]
                if deployed_models:
                    print(f"🎯 You have {len(deployed_models)} DEPLOYED model(s) ready for inference!")
                    print(f"   Recommended: Run 'python inference_app.py' to test inference and consume credits.")
                else:
                    print("⚠️  You have models, but none are currently in 'DEPLOYED' state.")
                    print("   You need to deploy a model before running inference.")
            print("-" * 60)
        elif response.status_code == 403 or response.status_code == 401:
            print("❌ Authentication Failed: Invalid or expired API Key.")
            print(f"Server response: {response.status_code} - {response.text}")
        else:
            print(f"⚠️  Unexpected response ({response.status_code}): {response.text}")

    except Exception as e:
        print(f"❌ Connection Error: {e}")
        print("Please check your internet connection or proxy settings.")

if __name__ == "__main__":
    main()
