import sys
import json
from pathlib import Path
import pandas as pd
import dataclasses

sys.path.append(str(Path("src").resolve()))

from core.config import load_settings
from retrieval.index import LocalEmbeddingIndex
from retrieval.agent import build_agent, run_agent_question

def run_checkpoint_6():
    print("=== BẮT ĐẦU CHECKPOINT 6: RAG & AGENT (REPAIRED) ===")
    settings = load_settings()
    
    repaired_json = Path("data/clean/papers_clean_repaired.json")
    if not repaired_json.exists():
        print(f"-> LỖI: Không tìm thấy file {repaired_json}.")
        return

    # 1. Đọc dữ liệu đã được phục hồi
    print(f"\n1. Đọc dữ liệu repaired từ {repaired_json}...")
    with open(repaired_json, 'r', encoding='utf-8') as f:
        records = json.load(f)
    df = pd.DataFrame(records)
    print(f"-> Đã load {len(df)} bài báo đã được phục hồi.")
    
    # 2. Build Index (tạo Embedding và nạp vào Chroma)
    print(f"\n2. Đang tạo Embeddings (MiniLM) và nạp vào collection '{settings.repaired_collection_name}'...")
    
    # Ép sử dụng collection name của repaired
    settings = dataclasses.replace(settings, baseline_collection_name=settings.repaired_collection_name)
    
    index = LocalEmbeddingIndex.build(
        df=df,
        settings=settings,
        embeddings_output_path=Path("data/embeddings/papers_embeddings_repaired.json")
    )
    print("-> Đã build Repaired Index thành công! Vector DB được lưu tại data/chroma/")
    
    # 3. Test Semantic Search
    query = "Large language models and AI safety"
    print(f"\n3. Test Semantic Search với query baseline: '{query}'")
    results = index.search(query, top_k=2)
    for i, res in enumerate(results, 1):
        print(f"\n   [Kết quả {i}] (Score: {res.score:.4f})")
        print(f"   - Title: {res.title}")
        print(f"   - Paper ID: {res.paper_id}")
        
    # 4. Test Exact Lookup
    if len(df) > 0:
        sample_id = df.iloc[0]["paper_id"]
        print(f"\n4. Test Exact Lookup với paper_id: '{sample_id}'")
        lookup_res = index.lookup(sample_id)
        if lookup_res:
            print(f"   -> Tìm thấy chính xác! Title: {lookup_res['title']}")
        else:
            print("   -> LỖI: Không tìm thấy bài báo.")
            
    # 5. Kiểm tra 3 collection độc lập
    print("\n5. Kiểm tra sự tồn tại của 3 collection (Baseline, Corrupted, Repaired)...")
    from chromadb import PersistentClient
    client = PersistentClient(path=str(settings.paths.chroma_dir))
    try:
        baseline_col = client.get_collection("papers-baseline")
        print(f"   -> OK: 'papers-baseline' có {baseline_col.count()} records.")
        
        corrupted_col = client.get_collection("papers-corrupted")
        print(f"   -> OK: 'papers-corrupted' có {corrupted_col.count()} records.")
        
        repaired_col = client.get_collection("papers-repaired")
        print(f"   -> OK: 'papers-repaired' có {repaired_col.count()} records.")
    except Exception as e:
        print(f"   -> LỖI khi kiểm tra 3 collections: {e}")
        
    print("\n=== CHECKPOINT 6 HOÀN TẤT ===")

if __name__ == "__main__":
    run_checkpoint_6()
