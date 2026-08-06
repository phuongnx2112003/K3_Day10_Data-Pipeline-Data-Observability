import sys
import json
from pathlib import Path
import pandas as pd

sys.path.append(str(Path("src").resolve()))

from core.config import load_settings
from retrieval.index import LocalEmbeddingIndex
from retrieval.agent import build_agent, run_agent_question

def run_checkpoint_2():
    print("=== BẮT ĐẦU CHECKPOINT 2: RAG & AGENT ===")
    settings = load_settings()
    
    # 1. Đọc dữ liệu sạch
    print("\n1. Đọc dữ liệu từ data/clean/papers_clean.json...")
    with open(settings.paths.clean_json, 'r', encoding='utf-8') as f:
        records = json.load(f)
    df = pd.DataFrame(records)
    print(f"-> Đã load {len(df)} bài báo.")
    
    # 2. Build Index (tạo Embedding và nạp vào Chroma)
    print(f"\n2. Đang tạo Embeddings (MiniLM) và nạp vào collection '{settings.baseline_collection_name}'...")
    
    index = LocalEmbeddingIndex.build(
        df=df,
        settings=settings,
        embeddings_output_path=settings.paths.embeddings_json
    )
    print("-> Đã build Index thành công! Vector DB được lưu tại data/chroma/")
    
    # 3. Test Semantic Search
    query = "Large language models and AI safety"
    print(f"\n3. Test Semantic Search với query: '{query}'")
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
            
    # 5. Test Agent
    print("\n5. Build Agent và kiểm thử (smoke test)...")
    try:
        agent = build_agent(settings, index)
        # Bắt agent tìm paper
        question = "What does the paper 'SafeRAG' talk about? Tell me based on the corpus."
        print(f"   -> Câu hỏi cho Agent: {question}")
        print("   -> Đang gọi Agent (Agent sẽ dùng tool để search corpus)...\n")
        answer = run_agent_question(agent, question)
        print(f"   [Agent Trả lời]:\n{answer}")
        
        print("\n-> Agent hoạt động tốt và đã sử dụng Tool để lấy thông tin.")
    except Exception as e:
        print(f"\n   -> Không thể chạy Agent (Lý do phổ biến: Chưa cấu hình LLM API Key trong file .env).")
        print(f"   Lỗi chi tiết: {e}")
        
    print("\n=== CHECKPOINT 2 HOÀN TẤT ===")

if __name__ == "__main__":
    run_checkpoint_2()
