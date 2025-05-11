import faiss

FAISS_PATH = "rag/vector_store.faiss"

index = faiss.read_index(FAISS_PATH)
print(f"[✔] FAISS index loaded.")
print(f"向量维度: {index.d}（应为 1536）")
print(f"向量数量: {index.ntotal}")

import json

with open("rag/metadata.json", "r", encoding="utf-8") as f:
    metadata = json.load(f)

print(f"[✔] Metadata 加载成功，共有 {len(metadata)} 条记录")
print("示例一条：")
print(json.dumps(metadata[0], indent=2, ensure_ascii=False))
assert index.ntotal == len(metadata), "向量数量与metadata不匹配"
