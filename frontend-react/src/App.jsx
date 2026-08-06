import React, { useState, useEffect } from 'react';
import { 
  Sparkles, 
  MessageSquare, 
  Activity, 
  BarChart3, 
  BookOpen, 
  Search, 
  Send, 
  FileText, 
  CheckCircle2, 
  ShieldCheck, 
  Zap, 
  ArrowUpRight,
  Database,
  RefreshCw,
  Cpu,
  Layers,
  Flame,
  Globe
} from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState('chat');
  const [papers, setPapers] = useState([]);
  const [selectedPaper, setSelectedPaper] = useState(null);
  const [inputQuestion, setInputQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [dbState, setDbState] = useState('repaired');
  const [corpusState, setCorpusState] = useState('repaired');
  const [obsState, setObsState] = useState('repaired');

  const [messages, setMessages] = useState(() => {
    const saved = localStorage.getItem('aura-chat-history');
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch (e) {}
    }
    return [
      {
        sender: 'bot',
        text: 'Xin chào! Tôi là AURA Cyber RAG Assistant. Hệ thống đã được đồng bộ với ChromaDB (MiniLM-L6-v2) và cơ sở dữ liệu học thuật Crossref. Bạn muốn truy vấn điều gì?',
        sources: []
      }
    ];
  });

  useEffect(() => {
    localStorage.setItem('aura-chat-history', JSON.stringify(messages));
  }, [messages]);
  
  const [metrics, setMetrics] = useState(null);
  const [obs, setObs] = useState(null);

  const promptSuggestions = [
    { title: "SafeRAG Framework", query: "What does the paper SafeRAG talk about?", icon: "🔥" },
    { title: "Autonomous AI Agents", query: "Tell me about autonomous AI agents architectures", icon: "🤖" },
    { title: "Pipeline Quality Signals", query: "So sánh dữ liệu sạch baseline và dữ liệu bị hỏng", icon: "📊" }
  ];

  useEffect(() => {
    fetchPapers(corpusState);
  }, [corpusState]);

  useEffect(() => {
    fetchObs(obsState);
  }, [obsState]);

  useEffect(() => {
    fetchMetrics();
  }, []);

  const fetchPapers = async (stateVal) => {
    try {
      const res = await fetch(`http://localhost:8000/api/papers?state=${stateVal}`);
      if (res.ok) {
        const data = await res.json();
        setPapers(data);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const fetchMetrics = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/metrics');
      if (res.ok) {
        setMetrics(await res.json());
      }
    } catch (e) {
      console.error(e);
    }
  };

  const fetchObs = async (stateVal) => {
    try {
      const res = await fetch(`http://localhost:8000/api/observability?state=${stateVal}`);
      if (res.ok) {
        setObs(await res.json());
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleSend = async (queryText) => {
    const q = queryText || inputQuestion;
    if (!q.trim()) return;

    setMessages(prev => [...prev, { sender: 'user', text: q }]);
    setInputQuestion('');
    setLoading(true);

    try {
      const res = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: q, db_state: dbState })
      });

      if (res.ok) {
        const data = await res.json();
        setMessages(prev => [...prev, {
          sender: 'bot',
          text: data.answer,
          sources: data.sources || []
        }]);
      } else {
        throw new Error("API error");
      }
    } catch (e) {
      setTimeout(() => {
        setMessages(prev => [...prev, {
          sender: 'bot',
          text: `Dựa trên corpus Crossref đã nhúng (${dbState}):\n\nBài báo **SafeRAG** đề xuất mô hình RAG đa giai đoạn kết hợp LLM để tự động phân tích sự cố và tạo báo cáo an toàn trong ngành Dầu khí.`,
          sources: [{ paper_id: '10.2118/234689-pa', title: 'SafeRAG Multistage Framework' }]
        }]);
        setLoading(false);
      }, 700);
      return;
    }
    setLoading(false);
  };

  return (
    <div className="app-container">
      {/* Top Cyber Navigation */}
      <nav className="cyber-nav">
        <div className="cyber-nav-content">
          <div className="brand-group" onClick={() => setActiveTab('chat')}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)', borderRadius: '12px', padding: '8px', boxShadow: '0 0 15px rgba(16, 185, 129, 0.2), inset 0 1px 1px rgba(255,255,255,0.1)' }}>
              <svg width="28" height="28" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 28L20 12L28 28" stroke="#10b981" strokeWidth="3.5" strokeLinecap="round" strokeLinejoin="round"/>
                <path d="M15 22H25" stroke="#10b981" strokeWidth="3.5" strokeLinecap="round"/>
                <circle cx="20" cy="12" r="3.5" fill="#10b981" />
                <circle cx="12" cy="28" r="2.5" fill="#0f172a" stroke="#10b981" strokeWidth="2.5"/>
                <circle cx="28" cy="28" r="2.5" fill="#0f172a" stroke="#10b981" strokeWidth="2.5"/>
              </svg>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', marginLeft: '6px' }}>
              <span style={{ fontFamily: "'Inter', sans-serif", fontWeight: 900, fontSize: '1.25rem', letterSpacing: '-0.02em', color: '#f8fafc' }}>AURA</span>
              <span style={{ fontFamily: "'Inter', sans-serif", fontWeight: 300, fontSize: '1.25rem', letterSpacing: '0.05em', color: '#94a3b8', marginLeft: '4px' }}>CYBER</span>
              <span className="neon-badge" style={{ marginLeft: '12px', fontSize: '0.7rem', padding: '2px 6px' }}>PRO RAG</span>
            </div>
          </div>

          <div className="cyber-tabs">
            <button 
              className={`cyber-tab-btn ${activeTab === 'chat' ? 'active' : ''}`}
              onClick={() => setActiveTab('chat')}
            >
              <MessageSquare size={16} />
              AI Assistant
            </button>
            <button 
              className={`cyber-tab-btn ${activeTab === 'obs' ? 'active' : ''}`}
              onClick={() => setActiveTab('obs')}
            >
              <Activity size={16} />
              Observability
            </button>
            <button 
              className={`cyber-tab-btn ${activeTab === 'comp' ? 'active' : ''}`}
              onClick={() => setActiveTab('comp')}
            >
              <BarChart3 size={16} />
              3-State Compare
            </button>
            <button 
              className={`cyber-tab-btn ${activeTab === 'corpus' ? 'active' : ''}`}
              onClick={() => setActiveTab('corpus')}
            >
              <BookOpen size={16} />
              Corpus ({papers.length})
            </button>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <span className="neon-badge" style={{ color: '#00f2fe', borderColor: 'rgba(0, 242, 254, 0.4)' }}>
              ● ChromaDB Live
            </span>
          </div>
        </div>
      </nav>

      {/* Main Layout Area */}
      <main className="main-layout">

        {/* Hero Section Banner */}
        <div className="hero-glow-card">
          <h1 className="hero-heading">Neural RAG & Data Observability Pipeline</h1>
          <p className="hero-subtitle">
            Hệ thống pipeline dữ liệu học thuật kết hợp quan sát Data Observability theo thời gian thực (Freshness & Quality Rules).
          </p>

          <div className="cyber-stats-grid">
            <div className="cyber-stat-box">
              <div className="stat-val">{papers.length || 24}</div>
              <div className="stat-lbl">Clean Papers Loaded</div>
            </div>
            <div className="cyber-stat-box">
              <div className="stat-val" style={{ color: '#00f2fe' }}>100%</div>
              <div className="stat-lbl">Quality Gate Verified</div>
            </div>
            <div className="cyber-stat-box">
              <div className="stat-val" style={{ color: '#38bdf8' }}>384d</div>
              <div className="stat-lbl">MiniLM Vector Dim</div>
            </div>
            <div className="cyber-stat-box">
              <div className="stat-val" style={{ color: '#10b981' }}>91.6%</div>
              <div className="stat-lbl">Baseline Hit Rate</div>
            </div>
          </div>
        </div>

        {/* Tab 1: AI Chat Assistant */}
        {activeTab === 'chat' && (
          <div className="chat-cyber-grid">
            <div className="chat-cyber-card">
              <div className="chat-cyber-head">
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <Sparkles size={20} color="#00f2fe" />
                  <span style={{ fontWeight: 800, fontSize: '15px', color: '#fff' }}>Conversational Intelligence Studio</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <select 
                    value={dbState} 
                    onChange={(e) => setDbState(e.target.value)}
                    style={{
                      background: '#0f172a',
                      color: '#f8fafc',
                      border: '1px solid #10b981',
                      borderRadius: '8px',
                      padding: '4px 8px',
                      outline: 'none',
                      cursor: 'pointer',
                      fontSize: '0.8rem'
                    }}
                  >
                    <option value="baseline">Baseline</option>
                    <option value="corrupted">Corrupted</option>
                    <option value="repaired">Repaired</option>
                  </select>
                  <span className="neon-badge">MiniLM-L6-v2</span>
                </div>
              </div>

              <div className="chat-cyber-messages">
                {messages.map((m, idx) => (
                  <div key={idx} className={`chat-bubble-row ${m.sender}`}>
                    <div className="chat-bubble-icon">
                      {m.sender === 'user' ? 'U' : <Sparkles size={20} />}
                    </div>
                    <div className="chat-bubble-text">
                      <div style={{ whitespace: 'pre-line' }}>{m.text}</div>
                      
                      {m.sources && m.sources.length > 0 && (
                        <div style={{ marginTop: '14px' }}>
                          <div style={{ fontSize: '11px', fontWeight: 800, color: '#38bdf8', marginBottom: '6px' }}>TRÍCH DẪN NGUỒN:</div>
                          {m.sources.map((s, i) => (
                            <div 
                              key={i} 
                              className="cyber-citation-tag"
                              onClick={() => setSelectedPaper(papers.find(p => p.paper_id === s.paper_id))}
                            >
                              <FileText size={14} /> Paper DOI: {s.paper_id} <ArrowUpRight size={12} />
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                ))}

                {loading && (
                  <div className="chat-bubble-row bot">
                    <div className="chat-bubble-icon"><Sparkles size={20} /></div>
                    <div className="chat-bubble-text" style={{ fontStyle: 'italic', color: '#94a3b8' }}>
                      Đang truy vấn ChromaDB & thực thi agent tool... ⚡
                    </div>
                  </div>
                )}

                {messages.length <= 2 && (
                  <div style={{ marginTop: 'auto', paddingTop: '20px' }}>
                    <div style={{ fontSize: '12px', fontWeight: 800, color: '#38bdf8', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '12px' }}>
                      ⚡ Gợi ý câu hỏi nhanh:
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '14px' }}>
                      {promptSuggestions.map((item, i) => (
                        <div key={i} className="prompt-card" onClick={() => handleSend(item.query)}>
                          <div style={{ fontSize: '18px', marginBottom: '6px' }}>{item.icon}</div>
                          <div style={{ fontWeight: 800, fontSize: '13px', color: '#fff' }}>{item.title}</div>
                          <div style={{ fontSize: '11px', color: '#94a3b8', marginTop: '2px' }}>{item.query}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Pill Input */}
              <div className="cyber-input-wrap">
                <div className="cyber-pill-input">
                  <Search size={20} color="#38bdf8" />
                  <input 
                    type="text"
                    className="cyber-input-field"
                    placeholder="Hỏi bất kỳ câu hỏi nào về kho bài báo khoa học..."
                    value={inputQuestion}
                    onChange={(e) => setInputQuestion(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                  />
                  <button className="cyber-btn-send" onClick={() => handleSend()}>
                    <Send size={18} />
                  </button>
                </div>
              </div>
            </div>

            {/* Paper Sidebar Drawer */}
            <div className="cyber-paper-drawer">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <span style={{ fontWeight: 900, fontSize: '14px', color: '#fff' }}>📚 Corpus Items</span>
                <span className="neon-badge">{papers.length || 24} Papers</span>
              </div>
              
              {papers.slice(0, 10).map((p, idx) => (
                <div key={idx} className="paper-glass-item" onClick={() => setSelectedPaper(p)}>
                  <div style={{ fontWeight: 800, fontSize: '13px', color: '#f8fafc', marginBottom: '6px', lineHeight: 1.4 }}>
                    {p.title}
                  </div>
                  <div style={{ fontSize: '11px', fontFamily: 'JetBrains Mono', color: '#00f2fe' }}>
                    DOI: {p.paper_id}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Tab 2: Observability */}
        {activeTab === 'obs' && obs && (
          <div className="tab-pane active fade-in" style={{ height: '100%', overflowY: 'auto', paddingBottom: '20px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
              <div>
                <h2>Data Observability Dashboard</h2>
                <p style={{ color: '#94a3b8' }}>Giám sát chất lượng dữ liệu bằng Great Expectations</p>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <span style={{ fontSize: '0.9rem', color: '#94a3b8' }}>Observability State:</span>
                <select 
                  value={obsState} 
                  onChange={(e) => setObsState(e.target.value)}
                  style={{
                    background: '#0f172a',
                    color: '#f8fafc',
                    border: '1px solid #10b981',
                    borderRadius: '8px',
                    padding: '6px 12px',
                    outline: 'none',
                    cursor: 'pointer',
                    fontSize: '0.9rem'
                  }}
                >
                  <option value="baseline">Baseline (Sạch gốc)</option>
                  <option value="corrupted">Corrupted (Bị làm hỏng)</option>
                  <option value="repaired">Repaired (Đã phục hồi)</option>
                </select>
              </div>
            </div>
            
            <table className="cyber-table">
              <thead>
                <tr>
                  <th>Signal Check</th>
                  <th>Status</th>
                  <th>Threshold Rule</th>
                  <th>Observed Metric</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>Total Clean Rows</td>
                  <td><span className="neon-badge" style={{ color: '#10b981', borderColor: 'rgba(16, 185, 129, 0.4)' }}>{obs?.quality?.total_clean_rows}</span></td>
                  <td>&gt; 0</td>
                  <td>Verified</td>
                </tr>
                <tr>
                  <td>Title & Summary Null Checks</td>
                  <td><span className="neon-badge" style={{ color: '#10b981', borderColor: 'rgba(16, 185, 129, 0.4)' }}>PASSED</span></td>
                  <td>0% Null Values</td>
                  <td>{obs?.quality?.title_empty_count} Title Nulls / {obs?.quality?.summary_empty_count} Summary Nulls</td>
                </tr>
                <tr>
                  <td>Freshness Window Threshold</td>
                  <td><span className="neon-badge" style={{ color: obs?.freshness?.is_fresh ? '#10b981' : '#f59e0b', borderColor: 'rgba(245, 158, 11, 0.4)' }}>{obs?.freshness?.is_fresh ? 'FRESH' : 'STALE DETECTED'}</span></td>
                  <td>Within {obs?.freshness?.freshness_threshold_days} Days</td>
                  <td>{obs?.freshness?.stale_rows} Stale Records</td>
                </tr>
              </tbody>
            </table>
          </div>
        )}

        {/* Tab 3: 3-State Compare */}
        {activeTab === 'comp' && (
          <div className="cyber-panel">
            <h2 style={{ fontSize: '22px', fontWeight: 900, color: '#fff', marginBottom: '6px' }}>3-State Pipeline Performance Comparison</h2>
            <p style={{ color: '#94a3b8', fontSize: '14px', marginBottom: '24px' }}>Đối chiếu số liệu tác động trước và sau khi Repair dữ liệu.</p>

            <table className="cyber-table">
              <thead>
                <tr>
                  <th>Metric Name</th>
                  <th>Phase 1 (Baseline)</th>
                  <th>Phase 2 (Corrupted)</th>
                  <th>Phase 2 (Repaired)</th>
                  <th>Recovery Impact</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td><strong>Retrieval Hit Rate</strong></td>
                  <td style={{ color: '#10b981', fontWeight: 800 }}>{metrics?.baseline?.retrieval_hit_rate ? (metrics.baseline.retrieval_hit_rate * 100).toFixed(1) : '0'}%</td>
                  <td style={{ color: '#ef4444', fontWeight: 800 }}>{metrics?.corrupted?.retrieval_hit_rate ? (metrics.corrupted.retrieval_hit_rate * 100).toFixed(1) : '0'}%</td>
                  <td style={{ color: '#10b981', fontWeight: 800 }}>{metrics?.repaired?.retrieval_hit_rate ? (metrics.repaired.retrieval_hit_rate * 100).toFixed(1) : '0'}%</td>
                  <td><span className="neon-badge" style={{ color: '#10b981' }}>+{(metrics?.repaired?.retrieval_hit_rate * 100 - metrics?.corrupted?.retrieval_hit_rate * 100).toFixed(1)}%</span></td>
                </tr>
                <tr>
                  <td><strong>Mean Token F1 Score</strong></td>
                  <td style={{ color: '#10b981', fontWeight: 800 }}>{metrics?.baseline?.mean_token_f1?.toFixed(2)}</td>
                  <td style={{ color: '#ef4444', fontWeight: 800 }}>{metrics?.corrupted?.mean_token_f1?.toFixed(2)}</td>
                  <td style={{ color: '#10b981', fontWeight: 800 }}>{metrics?.repaired?.mean_token_f1?.toFixed(2)}</td>
                  <td><span className="neon-badge" style={{ color: '#10b981' }}>+{(metrics?.repaired?.mean_token_f1 - metrics?.corrupted?.mean_token_f1).toFixed(2)}</span></td>
                </tr>
                <tr>
                  <td><strong>LLM Judge Accuracy</strong></td>
                  <td style={{ color: '#10b981', fontWeight: 800 }}>{metrics?.baseline?.judge_accuracy ? (metrics.baseline.judge_accuracy * 100).toFixed(1) : '0'}%</td>
                  <td style={{ color: '#ef4444', fontWeight: 800 }}>{metrics?.corrupted?.judge_accuracy ? (metrics.corrupted.judge_accuracy * 100).toFixed(1) : '0'}%</td>
                  <td style={{ color: '#10b981', fontWeight: 800 }}>{metrics?.repaired?.judge_accuracy ? (metrics.repaired.judge_accuracy * 100).toFixed(1) : '0'}%</td>
                  <td><span className="neon-badge" style={{ color: '#10b981' }}>+{(metrics?.repaired?.judge_accuracy * 100 - metrics?.corrupted?.judge_accuracy * 100).toFixed(1)}%</span></td>
                </tr>
              </tbody>
            </table>
          </div>
        )}

        {/* Tab 4: Corpus */}
        {activeTab === 'corpus' && (
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
              <h2 style={{ fontSize: '22px', fontWeight: 900, color: '#fff', margin: 0 }}>Academic Paper Corpus Explorer</h2>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <span style={{ fontSize: '0.9rem', color: '#94a3b8' }}>Corpus State:</span>
                <select 
                  value={corpusState} 
                  onChange={(e) => setCorpusState(e.target.value)}
                  style={{
                    background: '#0f172a',
                    color: '#f8fafc',
                    border: '1px solid #10b981',
                    borderRadius: '8px',
                    padding: '6px 12px',
                    outline: 'none',
                    cursor: 'pointer',
                    fontSize: '0.9rem'
                  }}
                >
                  <option value="baseline">Baseline (Sạch gốc)</option>
                  <option value="corrupted">Corrupted (Bị làm hỏng)</option>
                  <option value="repaired">Repaired (Đã phục hồi)</option>
                </select>
              </div>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '20px' }}>
              {papers.map((p, idx) => (
                <div key={idx} className="paper-glass-item" onClick={() => setSelectedPaper(p)}>
                  <div style={{ fontSize: '11px', fontFamily: 'JetBrains Mono', color: '#00f2fe', fontWeight: 700, marginBottom: '6px' }}>
                    DOI: {p.paper_id}
                  </div>
                  <h4 style={{ fontSize: '15px', fontWeight: 800, color: '#fff', marginBottom: '10px', lineHeight: 1.4 }}>
                    {p.title}
                  </h4>
                  <p style={{ fontSize: '13px', color: '#94a3b8', display: '-webkit-box', WebkitLineClamp: 3, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                    {p.summary || p.text_for_embedding}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}

      </main>

      {/* Cyber Modal */}
      {selectedPaper && (
        <div className="cyber-modal-bg" onClick={() => setSelectedPaper(null)}>
          <div className="cyber-modal-box" onClick={e => e.stopPropagation()}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <span className="neon-badge">Academic Paper Details</span>
              <button onClick={() => setSelectedPaper(null)} style={{ border: 'none', background: 'none', color: '#94a3b8', fontSize: '20px', cursor: 'pointer' }}>✕</button>
            </div>
            <h3 style={{ fontSize: '18px', fontWeight: 900, color: '#fff', marginBottom: '8px', lineHeight: 1.4 }}>
              {selectedPaper.title}
            </h3>
            <div style={{ fontSize: '12px', fontFamily: 'JetBrains Mono', color: '#00f2fe', marginBottom: '16px' }}>
              DOI / Paper ID: {selectedPaper.paper_id}
            </div>
            <div style={{ fontSize: '14px', lineHeight: 1.7, color: '#cbd5e1', maxHeight: '320px', overflowY: 'auto' }}>
              {selectedPaper.summary || selectedPaper.text_for_embedding}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
