import http.server
import socketserver
import json
import sys
from pathlib import Path

# Add src directory to sys.path
root_dir = Path(__file__).resolve().parents[1]
sys.path.append(str(root_dir / "src"))

from core.config import load_settings
from retrieval.index import LocalEmbeddingIndex
from retrieval.agent import build_agent, run_agent_question

PORT = 8000
FRONTEND_DIR = root_dir / "frontend"

settings = load_settings()
import dataclasses

index_caches = {}
agent_caches = {}

def get_index(db_state='baseline'):
    if db_state not in index_caches:
        try:
            # Map db_state to the actual collection name
            col_name = {
                'baseline': settings.baseline_collection_name,
                'corrupted': settings.corrupted_collection_name,
                'repaired': settings.repaired_collection_name
            }.get(db_state, settings.baseline_collection_name)
            
            custom_settings = dataclasses.replace(settings, baseline_collection_name=col_name)
            index_caches[db_state] = LocalEmbeddingIndex.load(custom_settings)
        except Exception as e:
            print(f"Could not load index for {db_state}: {e}")
            return None
    return index_caches[db_state]

def get_agent(db_state='baseline'):
    if db_state not in agent_caches:
        idx = get_index(db_state)
        if idx:
            try:
                agent_caches[db_state] = build_agent(settings, idx)
            except Exception as e:
                print(f"Could not build agent for {db_state}: {e}")
                return None
    return agent_caches.get(db_state)

class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(FRONTEND_DIR), **kwargs)

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        from urllib.parse import urlparse, parse_qs
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == "/api/papers":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            
            query_params = parse_qs(parsed_path.query)
            state = query_params.get('state', ['repaired'])[0]
            
            if state == 'baseline':
                clean_json_path = settings.paths.clean_json
            elif state == 'corrupted':
                clean_json_path = settings.paths.corrupted_clean_json
            else:
                clean_json_path = settings.paths.repaired_clean_json
                
            if clean_json_path.exists():
                with open(clean_json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            else:
                data = []
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
            return
            
        elif parsed_path.path == "/api/metrics":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            
            def load_json(p):
                return json.load(open(p, 'r')) if Path(p).exists() else {}
                
            data = {
                "baseline": load_json(settings.paths.baseline_metrics),
                "corrupted": load_json(settings.paths.corrupted_metrics),
                "repaired": load_json(settings.paths.repaired_metrics)
            }
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
            return
            
        elif parsed_path.path.startswith("/api/observability"):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            
            query_params = parse_qs(parsed_path.query)
            state = query_params.get('state', ['repaired'])[0]
            
            def load_json(p):
                return json.load(open(p, 'r')) if Path(p).exists() else {}
                
            q_file = settings.paths.quality_dir / f"{state}_quality.json"
            f_file = settings.paths.quality_dir / f"{state}_freshness.json"
            
            # fallback to freshness_report.json if specific state not found
            if not f_file.exists():
                f_file = settings.paths.freshness_report
                
            data = {
                "quality": load_json(q_file),
                "freshness": load_json(f_file)
            }
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
            return
            
        super().do_GET()

    def do_POST(self):
        if self.path == "/api/chat":
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length)
            payload = json.loads(body.decode('utf-8'))
            question = payload.get("question", "")
            db_state = payload.get("db_state", "baseline")
            
            agent = get_agent(db_state)
            idx = get_index(db_state)
            
            sources = []
            if idx:
                search_res = idx.search(question, top_k=2)
                sources = [{"paper_id": r.paper_id, "title": r.title} for r in search_res]

            if agent:
                try:
                    answer = run_agent_question(agent, question)
                    if not isinstance(answer, str):
                        answer = str(answer)
                except Exception as e:
                    answer = f"Đã xảy ra lỗi khi gọi Agent: {e}"
            else:
                answer = "Hệ thống RAG Agent đang ở chế độ Offline (Chưa cấu hình API Key LLM)."

            response_data = {
                "answer": answer,
                "sources": sources
            }

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode("utf-8"))
            return

        self.send_error(404)

def run_server():
    print(f"==================================================")
    print(f"🚀 AURA Web UI Server running at: http://localhost:{PORT}")
    print(f"==================================================")
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), CustomHandler) as httpd:
        httpd.serve_forever()

if __name__ == "__main__":
    run_server()
