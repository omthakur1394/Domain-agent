import os
import sys
import time
import json
import requests
from dotenv import load_dotenv
from docling.document_converter import DocumentConverter

load_dotenv()

API_KEY = os.getenv("NUGEN_API_KEY", "").strip()
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
selected_papers = []
for p in all_pdf_paths:
    base = os.path.basename(p)
    if base not in seen:
        seen.add(base)
        selected_papers.append(p)

print("doing the converting pdf into the markdowns")

converter = DocumentConverter()
markdown_chunks = []

for pdf_path in selected_papers:
    try:
        result = converter.convert(pdf_path)
        md_text = result.document.export_to_markdown()
        markdown_chunks.append({
            "filename": os.path.basename(pdf_path),
            "content": md_text
        })
    except Exception:
        pass

print("make the textfile")

os.makedirs("DATA", exist_ok=True)
BATCH_SIZE = 25
batch_files = []
num_batches = (len(markdown_chunks) + BATCH_SIZE - 1) // BATCH_SIZE

for b_idx in range(num_batches):
    start = b_idx * BATCH_SIZE
    end = min(start + BATCH_SIZE, len(markdown_chunks))
    batch_items = markdown_chunks[start:end]
    
    batch_content = "\n\n".join(
        f"# {item['filename']}\n\n{item['content']}" for item in batch_items
    )
    
    out_file = f"DATA/docling_markdown_batch_{b_idx + 1}.txt"
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(batch_content)
    batch_files.append((b_idx + 1, out_file, len(batch_items)))

print("uploading")

headers = {"Authorization": f"Bearer {API_KEY}"}
upload_results = []

for b_num, file_path, paper_count in batch_files:
    fname = os.path.basename(file_path)
    payload = {"categories": "text/plain", "names": fname}
    
    try:
        with open(file_path, "rb") as f:
            files = {"files": (fname, f)}
            res = requests.post(f"{BASE_URL}/api/v3/documents/create", headers=headers, data=payload, files=files, timeout=60)
            
        if res.status_code in (200, 201):
            doc_id = res.json().get("document_ids", [])[0]
        elif res.status_code == 409:
            doc_id = res.json().get("detail", {}).get("document_id")
        else:
            continue
            
        for _ in range(15):
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

with open("DATA/uploaded_docling_manifest.json", "w", encoding="utf-8") as out:
    json.dump(upload_results, out, indent=2)

