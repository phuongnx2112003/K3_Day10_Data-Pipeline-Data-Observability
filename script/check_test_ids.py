import json
from pathlib import Path

def check_testset_ids():
    # Paths
    test_set_path = Path("data/eval/test_set.json")
    clean_json_path = Path("data/clean/papers_clean.json")
    
    if not test_set_path.exists():
        print(f"Lỗi: Không tìm thấy file {test_set_path}")
        return
        
    if not clean_json_path.exists():
        print(f"Lỗi: Không tìm thấy file {clean_json_path}")
        return
        
    # Load test set
    with open(test_set_path, "r", encoding="utf-8") as f:
        test_set = json.load(f)
        
    # Load clean data to get available IDs
    with open(clean_json_path, "r", encoding="utf-8") as f:
        clean_data = json.load(f)
        
    available_ids = {str(item.get("paper_id")).strip().lower() for item in clean_data}
    
    # Check IDs
    print(f"Đã load {len(test_set)} câu hỏi từ test_set.json.")
    print(f"Đã load {len(available_ids)} paper_id hợp lệ từ database (clean data).")
    
    missing_ids = set()
    total_doc_ids = 0
    
    for idx, item in enumerate(test_set):
        doc_ids = item.get("ground_truth_doc_ids", [])
        if not doc_ids:
            print(f"Cảnh báo: Câu hỏi {idx+1} (ID: {item.get('id')}) không có ground_truth_doc_ids!")
            continue
            
        for doc_id in doc_ids:
            total_doc_ids += 1
            # Check lowercase string exact match as per index logic
            if str(doc_id).strip().lower() not in available_ids:
                missing_ids.add(doc_id)
                
    print("\n--- KẾT QUẢ KIỂM TRA ---")
    if not missing_ids:
        print("✅ TOÀN BỘ hợp lệ! Tất cả ground_truth_doc_ids trong test_set đều tồn tại trong Vector DB.")
    else:
        print(f"❌ PHÁT HIỆN LỖI: Có {len(missing_ids)} ID bài báo trong test_set KHÔNG tồn tại trong Vector DB!")
        print("Danh sách các ID bị thiếu:")
        for missing_id in missing_ids:
            print(f"   - {missing_id}")
            
if __name__ == "__main__":
    check_testset_ids()
