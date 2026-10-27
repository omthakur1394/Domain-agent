---
name: nugen-ecommerce-alignment
description: End-to-end skill and operational playbook for fine-tuning/aligning foundation models on e-commerce domain data using Nugen Intelligence, and executing automated inference workloads to achieve the $100+ API credit consumption requirement.
---

# Nugen E-Commerce Domain Alignment & Workload Skill

This skill documents the complete operational procedure to take raw e-commerce knowledge base documents (ShopEase policies, customer support rules, seller guidelines), fine-tune/align foundation models on the **Nugen Intelligence** platform, and execute batch inference workloads to consume **$100+** in promotional API credits.

---

## 🎯 Program Objectives & Rules

1. **Promotional Allocation:** $150 in API credits provided upon signup via invitation.
2. **Usage Target:** Consume **>$100** of allocated credits (stretch goal: full $150).
3. **CRITICAL CHALLENGE RULE:**
   > Only inference traffic routed through **DOMAIN-ALIGNED MODELS** counts toward the program requirement. Calls to generic/base models **do not count**.
   > You must align and deploy at least one model before running workloads.

---

## 📁 Workspace Architecture

```
Testing-api/
├── DATA/                                             # Domain E-Commerce Knowledge Base
│   ├── ShopEase Category-Specific Policy Knowledge .pdf
│   ├── ShopEase Customer Support Knowledge Base (2).pdf
│   ├── ShopEase Legal, Escalations & Compliance KB.pdf
│   ├── ShopEase Promotions, Sales & Loyalty KB.pdf
│   ├── ShopEase Seller & Marketplace Policies KB.pdf
│   ├── ShopEase_Customer_Support_Knowledge_Base1.pdf
│   └── shopease_ecommerce_knowledge_base.txt        # Consolidated domain text (60k+ chars)
├── .env                                              # Nugen API Key & Base URL
├── .env.example                                      # Template configuration
├── align_model.py                                    # Automated 5-step alignment & deployment pipeline
├── inference_app.py                                  # Workload engine & interactive chat
├── test_connection.py                                # API key & deployed models verifier
├── deployed_model.json                               # Active deployed model metadata
├── README.md                                         # Project documentation
└── SKILL.md                                          # This skill playbook
```

---

## ⚙️ Prerequisites & Setup

### 1. Authentication
Ensure `.env` contains your active Nugen API Key:
```env
NUGEN_API_KEY=nugen-8b4f1a23aedc3048
NUGEN_BASE_URL=https://api.nugen.in
```

### 2. Verify Connection
Run `test_connection.py` to authenticate and inspect deployed models:
```powershell
python test_connection.py
```

Expected output:
```
============================================================
 🚀 NUGEN INTELLIGENCE - CONNECTION & MODELS CHECK
============================================================
1. Testing API Key against https://api.nugen.in...
✅ Authentication Successful!
```

---

## 🤖 Step 1: Fine-Tune / Align the E-Commerce Model

The alignment pipeline automates the 5-step Nugen lifecycle:
1. **Document Ingestion:** Uploads `DATA/shopease_ecommerce_knowledge_base.txt` to `POST /api/v3/documents/create`.
2. **Document Processing:** Polls `GET /api/v3/documents/{id}/status` until `READY`.
3. **Benchmark Generation:** Generates domain Q&A pairs via `POST /api/v3/benchmarks/create`.
4. **Alignment Training:** Triggers project creation via `POST /api/v3/alignment-projects/create` and polls status until `READY`.
5. **Deployment:** Deploys the aligned model via `POST /api/v3/models/{model_id}/deployment` and stores the active ID in `deployed_model.json`.

### Execution Command:
```powershell
python align_model.py --auto --name "ShopEase E-Commerce Model" --base-model "Qwen/Qwen2.5-0.5B-Instruct"
```

*Supported Base Models:*
- `Qwen/Qwen2.5-0.5B-Instruct` (Fastest alignment & high throughput)
- `meta-llama/Llama-3.2-3B-Instruct` (High-reasoning 3B parameter model)
- `Qwen/Qwen2.5-1.5B-Instruct`

---

## 📈 Step 2: Run Workloads to Consume >$100 Credits

To satisfy the **>$100** credit consumption target without manual prompt typing, run the automated batch workload runner.

### Execution Command:
```powershell
python inference_app.py
```
1. Select **Option 2** (`Run Workload / Batch Inference`).
2. Input the number of query batches (e.g. `20` to `50` batches).
3. The runner continuously executes domain inquiries across:
   - Return & refund eligibility on open-box electronics.
   - Damaged/counterfeit escalation workflows.
   - Lost-in-transit delivery SLAs and carrier compensation.
   - Coupon stacking & loyalty reward rules.
   - Seller late-fulfillment penalties.
   - Category-specific return windows for apparel & tech.
4. Token consumption and request metrics are calculated and logged after each run.

### Interactive Verification:
To verify domain answers interactively:
```powershell
python inference_app.py
```
Select **Option 1** to chat directly with your aligned model.

---

## 📊 Step 3: Monitoring Credit Consumption

1. Open your browser and log in to:  
   👉 **[https://platform.nugen.in](https://platform.nugen.in)**
2. Navigate to the **Usage / Billing** section.
3. Confirm that **Aligned Model Inference** credit usage has surpassed **$100**.
4. Once above $100, your program milestone is achieved!

