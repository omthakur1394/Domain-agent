import os
import sys
import time
import json
import fitz
import requests
from dotenv import load_dotenv

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

load_dotenv()
API_KEY = os.getenv("NUGEN_API_KEY")
BASE_URL = os.getenv("NUGEN_BASE_URL", "https://api.nugen.in").rstrip("/")

if not API_KEY:
    sys.exit(1)

classic_dir = "ai_papers/classic_ai_papers"
modern_dir = "ai_papers/ai_papers"

all_pdf_paths = []
if os.path.exists(classic_dir):
    all_pdf_paths += [os.path.join(classic_dir, f) for f in sorted(os.listdir(classic_dir)) if f.endswith(".pdf")]
if os.path.exists(modern_dir):
    all_pdf_paths += [os.path.join(modern_dir, f) for f in sorted(os.listdir(modern_dir)) if f.endswith(".pdf")]

seen = set()
selected_200 = []
for p in all_pdf_paths:
    base = os.path.basename(p)
    if base not in seen:
        seen.add(base)
        selected_200.append(p)
    if len(selected_200) == 200:
        break

BATCH_SIZE = 25
num_batches = (len(selected_200) + BATCH_SIZE - 1) // BATCH_SIZE
os.makedirs("DATA", exist_ok=True)

batch_files = []
for b_idx in range(num_batches):
    start = b_idx * BATCH_SIZE
    end = min(start + BATCH_SIZE, len(selected_200))
    batch_papers = selected_200[start:end]
    
    corpus = []
    for p_idx, path in enumerate(batch_papers, start + 1):
        f_name = os.path.basename(path)
        try:
            doc = fitz.open(path)
            text = ""
            for page_num in range(min(3, len(doc))):
                text += doc[page_num].get_text() + "\n"
            doc.close()
            corpus.append(f"PAPER {p_idx}: {f_name}\n" + text.strip())
        except Exception:
            pass
            
    full_text = "\n\n".join(corpus)
    out_file = f"DATA/research_batch_{b_idx + 1}.txt"
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(full_text)
    batch_files.append((b_idx + 1, out_file, len(batch_papers)))

headers = {"Authorization": f"Bearer {API_KEY}"}
upload_results = []

for b_num, file_path, paper_count in batch_files:
    fname = os.path.basename(file_path)
    payload = {"categories": "text/plain", "names": fname}
    
    try:
        with open(file_path, "rb") as f:
            files = {"files": (fname, f)}
            res = requests.post(f"{BASE_URL}/api/v3/documents/create", headers=headers, data=payload, files=files, timeout=45)
            
        if res.status_code in (200, 201):
            doc_id = res.json().get("document_ids", [])[0]
        elif res.status_code == 409:
            doc_id = res.json().get("detail", {}).get("document_id")
        else:
            continue
            
        for _ in range(12):
            s_res = requests.get(f"{BASE_URL}/api/v3/documents/{doc_id}/status", headers=headers, timeout=15)
            if s_res.json().get("status") == "READY":
                break
            time.sleep(3)
            
        upload_results.append({
            "batch_number": b_num,
            "filename": fname,
            "document_id": doc_id,
            "papers_count": paper_count,
            "status": "READY"
        })
    except Exception:
        pass

with open("DATA/uploaded_200_papers.json", "w", encoding="utf-8") as out:
    json.dump(upload_results, out, indent=2)
