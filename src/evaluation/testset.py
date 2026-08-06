from pathlib import Path
from typing import Any

import pandas as pd

from core.utils import write_json


def build_test_set(df: pd.DataFrame, output_path: str | Path) -> list[dict[str, Any]]:
    """Tạo bộ evaluation set từ cleaned dataframe.

    Yêu cầu cấu trúc mỗi sample:
    - id: Unique ID
    - question_type: 'summary' | 'authors' | 'date' | 'categories'
    - question: Câu hỏi kiểm thử
    - ground_truth: Câu trả lời mẫu chuẩn
    - ground_truth_doc_ids: List các paper_id làm bằng chứng (ground truth)
    """
    if df.empty:
        raise ValueError("Cannot build test set from an empty DataFrame.")

    test_set: list[dict[str, Any]] = []
    sample_index = 1

    # Duyệt qua các bài báo trong DataFrame để tạo câu hỏi
    for _, row in df.iterrows():
        paper_id = str(row.get("paper_id", "")).strip()
        title = str(row.get("title", "")).strip()
        summary = str(row.get("summary", "")).strip()
        authors = str(row.get("authors_joined", "")).strip()
        published = str(row.get("published", "")).strip()
        categories = str(row.get("categories_joined", "")).strip()

        if not paper_id or not title:
            continue

        # 1. Câu hỏi dạng Summary (Nội dung tóm tắt)
        if summary and summary.lower() != "nan":
            test_set.append(
                {
                    "id": f"q_{sample_index:03d}_summary",
                    "question_type": "summary",
                    "question": f"What is the main finding or summary of the paper '{title}'?",
                    "ground_truth": summary,
                    "ground_truth_doc_ids": [paper_id],
                }
            )
            sample_index += 1

        # 2. Câu hỏi dạng Authors (Tác giả)
        if authors and authors.lower() != "nan":
            test_set.append(
                {
                    "id": f"q_{sample_index:03d}_authors",
                    "question_type": "authors",
                    "question": f"Who are the authors of the paper '{title}'?",
                    "ground_truth": authors,
                    "ground_truth_doc_ids": [paper_id],
                }
            )
            sample_index += 1

        # 3. Câu hỏi dạng Date (Ngày xuất bản)
        if published and published.lower() != "nan":
            test_set.append(
                {
                    "id": f"q_{sample_index:03d}_date",
                    "question_type": "date",
                    "question": f"When was the paper '{title}' published?",
                    "ground_truth": published,
                    "ground_truth_doc_ids": [paper_id],
                }
            )
            sample_index += 1

        # 4. Câu hỏi dạng Categories (Lĩnh vực / Chủ đề)
        if categories and categories.lower() != "nan":
            test_set.append(
                {
                    "id": f"q_{sample_index:03d}_categories",
                    "question_type": "categories",
                    "question": f"What categories or subjects does the paper '{title}' cover?",
                    "ground_truth": categories,
                    "ground_truth_doc_ids": [paper_id],
                }
            )
            sample_index += 1


    output_path = Path(output_path)
    write_json(output_path, test_set)
    return test_set

