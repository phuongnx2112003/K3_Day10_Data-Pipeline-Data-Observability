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
index_cache = None
agent_cache = None

def get_index():
    global index_cache
    if index_cache is None:
        try:
            index_cache = LocalEmbeddingIndex.load(settings)
        except Exception as e:
            print(f"Could not load index: {e}")
    return index_cache

def get_agent():
    global agent_cache
    if agent_cache is None:
        idx = get_index()
        if idx:
            try:
                agent_cache = build_agent(settings, idx)
            except Exception as e:
                print(f"Could not build agent: {e}")
    return agent_cache

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
        if self.path == "/api/papers":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            
            # Đổi sang đọc file repaired để demo
            clean_json_path = root_dir / "data" / "clean" / "papers_clean_repaired.json"
            if clean_json_path.exists():
                with open(clean_json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            else:
                data = []
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
            return
            
        elif self.path == "/api/metrics":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            
            def load_json(p):
                return json.load(open(p, 'r')) if Path(p).exists() else {}
                
            data = {
                "baseline": load_json(settings.paths.results_dir / "baseline_metrics.json"),
                "corrupted": load_json(settings.paths.results_dir / "corrupted_metrics.json"),
                "repaired": load_json(settings.paths.results_dir / "repaired_metrics.json")
            }
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
            return
            
        elif self.path == "/api/observability":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            
            def load_json(p):
                return json.load(open(p, 'r')) if Path(p).exists() else {}
                
            data = {
                "quality": load_json(settings.paths.quality_dir / "repaired_quality.json"),
                "freshness": load_json(settings.paths.quality_dir / "repaired_freshness.json")
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
            
            agent = get_agent()
            idx = get_index()
            
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
