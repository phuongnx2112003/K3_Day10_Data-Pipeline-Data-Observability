import sys
import json
from pathlib import Path
import pandas as pd

sys.path.append(str(Path("src").resolve()))

from core.config import load_settings
from retrieval.index import LocalEmbeddingIndex
from retrieval.agent import build_agent, run_agent_question

def run_checkpoint_5():
    print("=== BẮT ĐẦU CHECKPOINT 5: RAG & AGENT (CORRUPTED) ===")
    settings = load_settings()
    
    corrupted_json = Path("data/clean/papers_clean_corrupted.json")
    if not corrupted_json.exists():
        print(f"-> LỖI: Không tìm thấy file {corrupted_json}. Thành viên 3 chưa chạy corruption flow?")
        return

    # 1. Đọc dữ liệu bị làm hỏng
    print(f"\n1. Đọc dữ liệu corrupted từ {corrupted_json}...")
    with open(corrupted_json, 'r', encoding='utf-8') as f:
        records = json.load(f)
    df = pd.DataFrame(records)
    print(f"-> Đã load {len(df)} bài báo bị làm hỏng.")
    
    # 2. Build Index (tạo Embedding và nạp vào Chroma)
    print(f"\n2. Đang tạo Embeddings (MiniLM) và nạp vào collection '{settings.corrupted_collection_name}'...")
    
    import dataclasses
    settings = dataclasses.replace(settings, baseline_collection_name=settings.corrupted_collection_name)
    
    index = LocalEmbeddingIndex.build(
        df=df,
        settings=settings,
        embeddings_output_path=Path("data/embeddings/papers_embeddings_corrupted.json")
    )
    print("-> Đã build Corrupted Index thành công! Vector DB được lưu tại data/chroma/")
    
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
            
    # 5. Check baseline integrity
    print("\n5. Kiểm tra tính toàn vẹn của baseline collection...")
    from chromadb import PersistentClient
    client = PersistentClient(path=str(settings.paths.chroma_db_dir))
    try:
        baseline_col = client.get_collection("papers-baseline")
        print(f"   -> OK: Collection 'papers-baseline' vẫn tồn tại với {baseline_col.count()} records.")
    except Exception as e:
        print(f"   -> LỖI: Collection 'papers-baseline' bị mất hoặc hỏng! {e}")
        
    print("\n=== CHECKPOINT 5 HOÀN TẤT ===")

if __name__ == "__main__":
    run_checkpoint_5()
