import sys
from pathlib import Path
import pandas as pd
import json

# Add src to sys.path so we can import core modules
sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from core.config import load_settings

def test_config_and_data():
    print("Loading settings...")
    settings = load_settings()
    
    clean_csv_path = settings.paths.clean_csv
    clean_json_path = settings.paths.clean_json
    
    print(f"Expected clean CSV path: {clean_csv_path}")
    print(f"Expected clean JSON path: {clean_json_path}")
    
    if not clean_json_path.exists() and not clean_csv_path.exists():
        print("\n[WARNING] Clean data files do not exist yet. Please wait for Vai trò 3 (Clean) to push.")
        return
        
    print("\n[SUCCESS] Clean data found! Proceeding to validation...")
    
    # Try reading dataframe (prefer JSON if exists, otherwise CSV)
    if clean_json_path.exists():
        with open(clean_json_path, 'r', encoding='utf-8') as f:
            records = json.load(f)
        df = pd.DataFrame(records)
    else:
        df = pd.read_csv(clean_csv_path)
        
    print(f"\nDataframe loaded with {len(df)} records.")
    
    # Verify required columns for LocalEmbeddingIndex
    required_cols = [
        "paper_id", "title", "text_for_embedding", "published", 
        "authors_joined", "categories_joined", "summary", 
        "abs_url", "pdf_url"
    ]
    
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        print(f"[ERROR] Dataframe is missing required columns for index: {missing_cols}")
    else:
        print("[SUCCESS] Dataframe has all required columns.")
        
        # Verify text_for_embedding is not empty
        empty_texts = df[df["text_for_embedding"].isna() | (df["text_for_embedding"].str.strip() == "")]
        if not empty_texts.empty:
            print(f"[WARNING] Found {len(empty_texts)} records with empty text_for_embedding!")
        else:
            print("[SUCCESS] All records have valid text_for_embedding.")
            
            # Print a sample to visually inspect
            print("\n--- SAMPLE text_for_embedding ---")
            print(df["text_for_embedding"].iloc[0][:500] + "...\n")
            
    print("\nNext step: If all validations pass, you are ready to build the LocalEmbeddingIndex in Checkpoint 2.")

if __name__ == "__main__":
    test_config_and_data()
