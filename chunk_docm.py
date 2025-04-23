import fitz  # PyMuPDF
import os
import re
import json

# File paths
pdf_path = "raw/ADM__V2_with_2024_amendments.pdf"
output_path = "chunks/docm_chunks.jsonl"

# Load PDF
doc = fitz.open(pdf_path)
full_text = ""

for page in doc:
    full_text += page.get_text()

# Clean spacing
full_text = re.sub(r"\n{2,}", "\n", full_text)
full_text = re.sub(r" {2,}", " ", full_text)

# Split into chunks by heading or paragraph
raw_chunks = re.split(r"\n(?=[0-9]+\.\d+|Diagram \d+|Section [A-Z])", full_text)

# Further split long chunks
final_chunks = []
for chunk in raw_chunks:
    if len(chunk.strip()) < 100:
        continue
    paragraphs = re.split(r"\n", chunk.strip())
    temp = ""
    for para in paragraphs:
        if len(temp) + len(para) > 800:
            final_chunks.append(temp.strip())
            temp = para
        else:
            temp += " " + para
    if temp:
        final_chunks.append(temp.strip())

# Write to JSONL
os.makedirs("chunks", exist_ok=True)
with open(output_path, "w") as f:
    for i, chunk in enumerate(final_chunks):
        f.write(json.dumps({
            "id": f"chunk_{i+1}",
            "text": chunk
        }) + "\n")

print(f"✅ Chunked {len(final_chunks)} text sections from Document M.")
print(f"Saved to: {output_path}")

