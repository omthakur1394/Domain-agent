# ShopEase E-Commerce AI - Nugen Domain Alignment

This repository implements an end-to-end domain-aligned AI system for **ShopEase E-Commerce** using the **Nugen Intelligence** API.

The project aligns foundation models on proprietary ShopEase customer support, seller policy, escalation, and legal documentation, and executes automated inference workloads to satisfy the Nugen developer credit program ($100+ usage target).

---

## 📁 Repository Contents

* `DATA/`: ShopEase E-Commerce Knowledge Base (PDFs + 60,000+ character consolidated domain text `shopease_ecommerce_knowledge_base.txt`).
* `align_model.py`: Automated pipeline for uploading documents, generating benchmarks, training alignment projects, and deploying models.
* `inference_app.py`: High-throughput workload generator & interactive chat client for deployed aligned models.
* `test_connection.py`: API connection, authentication, and deployed model inspector.
* `deployed_model.json`: Active deployed model metadata and ID.
* `SKILL.md`: Detailed Antigravity operational skill guide.
* `.env`: Stores Nugen API credentials.

---

## ⚡ Quick Start

### 1. Check API Connection
```powershell
python test_connection.py
```

### 2. Align an E-Commerce Model
```powershell
python align_model.py --auto --name "ShopEase E-Commerce Model"
```

### 3. Run Inference Workloads (To hit $100+ credit target)
```powershell
python inference_app.py
```
Select **Option 2** to run automated batch workloads through your aligned model.

---

## 📖 Complete Documentation
For full instructions, architecture details, and troubleshooting, see [SKILL.md](file:///c:/Users/ASUS/Desktop/Testing-api/SKILL.md).

