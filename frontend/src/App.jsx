import React, { useState, useEffect, useRef } from 'react';

const API_BASE = "http://localhost:8001/api";

function App() {
  const [user, setUser] = useState(null);
  const [isRegistering, setIsRegistering] = useState(false);
  const [authForm, setAuthForm] = useState({ username: '', password: '' });
  
  const [repoUrl, setRepoUrl] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [logs, setLogs] = useState([]);
  const [report, setReport] = useState(null);
  const [taskId, setTaskId] = useState(null);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('analyze'); // 'analyze' or 'history'
  const [history, setHistory] = useState([]);
  
  const terminalRef = useRef(null);

  // Check for existing session
  useEffect(() => {
    const savedUser = localStorage.getItem('user');
    const token = localStorage.getItem('token');
    if (savedUser && token) {
      setUser(JSON.parse(savedUser));
    }
  }, []);

  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [logs]);

  // Fetch history when tab changes
  useEffect(() => {
    if (activeTab === 'history' && user) {
      fetchHistory();
    }
  }, [activeTab]);

  const fetchHistory = async () => {
    try {
      const res = await fetch(`${API_BASE}/tasks`, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });
      if (res.ok) {
        const data = await res.json();
        setHistory(data);
      }
    } catch (err) {
      console.error("Failed to fetch history", err);
    }
  };

  const handleAuth = async (e) => {
    e.preventDefault();
    const endpoint = isRegistering ? '/auth/register' : '/auth/login';
    
    try {
      let body;
      let headers = { 'Content-Type': 'application/json' };
      
      if (isRegistering) {
        body = JSON.stringify(authForm);
      } else {
        const formData = new FormData();
        formData.append('username', authForm.username);
        formData.append('password', authForm.password);
        body = formData;
        headers = {};
      }

      const res = await fetch(`${API_BASE}${endpoint}`, {
        method: 'POST',
        headers,
        body
      });

      const data = await res.json();
      if (res.ok) {
        if (isRegistering) {
          setIsRegistering(false);
          setError("Registration successful! Please login.");
        } else {
          localStorage.setItem('token', data.access_token);
          localStorage.setItem('user', JSON.stringify(data.user));
          setUser(data.user);
          setError(null);
        }
      } else {
        setError(data.detail || "Authentication failed");
      }
    } catch (err) {
      setError("Server connection failed");
    }
  };

  const handleAnalyze = async () => {
    if (!repoUrl) return;
    setIsAnalyzing(true);
    setLogs([]);
    setReport(null);
    setError(null);

    try {
      const res = await fetch(`${API_BASE}/analyze`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({ repo_url: repoUrl }),
      });
      
      const data = await res.json();
      if (res.ok) {
        setTaskId(data.task_id);
      } else {
        setError(data.detail || "Analysis failed to start.");
        setIsAnalyzing(false);
      }
    } catch (err) {
      setError("Backend server is unreachable.");
      setIsAnalyzing(false);
    }
  };

  useEffect(() => {
    if (!taskId) return;

    const eventSource = new EventSource(`${API_BASE}/stream/${taskId}`);
    
    eventSource.onmessage = (event) => {
      if (event.data === "[DONE]") {
        eventSource.close();
        setIsAnalyzing(false);
        fetchHistory();
        return;
      }
      
      if (event.data.startsWith("[REPORT]")) {
        const reportData = JSON.parse(event.data.substring(8));
        setReport(reportData);
      } else {
        setLogs(prev => [...prev, event.data]);
      }
    };

    eventSource.onerror = () => {
      setError("Connection to agent lost.");
      eventSource.close();
      setIsAnalyzing(false);
    };

    return () => eventSource.close();
  }, [taskId]);

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setUser(null);
    setLogs([]);
    setReport(null);
  };

  if (!user) {
    return (
      <div className="auth-container">
        <div className="background-shapes">
          <div className="shape shape-1"></div>
          <div className="shape shape-2"></div>
        </div>
        
        <div className="glass-panel auth-card">
          <h1>{isRegistering ? 'Join Antigravity' : 'Welcome Back'}</h1>
          <p className="subtitle">Autonomous AI Testing Agent</p>
          
          <form onSubmit={handleAuth}>
            <input 
              type="text" 
              placeholder="Username" 
              required
              className="glass-input"
              value={authForm.username}
              onChange={(e) => setAuthForm({...authForm, username: e.target.value})}
            />
            <input 
              type="password" 
              placeholder="Password" 
              required
              className="glass-input"
              value={authForm.password}
              onChange={(e) => setAuthForm({...authForm, password: e.target.value})}
            />
            {error && <div className="error-msg">{error}</div>}
            <button type="submit" className="glow-button">
              {isRegistering ? 'Sign Up' : 'Sign In'}
            </button>
          </form>
          
          <p className="toggle-auth">
            {isRegistering ? 'Already have an account?' : "Don't have an account?"}
            <span onClick={() => { setIsRegistering(!isRegistering); setError(null); }}>
              {isRegistering ? ' Sign In' : ' Sign Up'}
            </span>
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="app-container">
      <div className="background-shapes">
        <div className="shape shape-1"></div>
        <div className="shape shape-2"></div>
        <div className="shape shape-3"></div>
      </div>

      <header className="glass-panel main-header auth-header">
        <div className="logo-section">
          <span className="logo-spark">✨</span>
          <h1>ANTIGRAVITY <span className="logo-tag">AI</span></h1>
        </div>
        <nav className="header-nav">
          <button 
            className={`nav-link ${activeTab === 'analyze' ? 'active' : ''}`}
            onClick={() => setActiveTab('analyze')}
          >
            Analyze
          </button>
          <button 
            className={`nav-link ${activeTab === 'history' ? 'active' : ''}`}
            onClick={() => setActiveTab('history')}
          >
            History
          </button>
          <div className="user-profile">
            <span className="username">{user.username}</span>
            <button className="logout-btn" onClick={handleLogout}>Logout</button>
          </div>
        </nav>
      </header>

      <main className="main-content">
        {activeTab === 'analyze' ? (
          <div className="analysis-view animate-fade-in-up">
            <section className="glass-panel hero-section">
              <h2>Autonomous <span className="highlight">Test Generation</span></h2>
              <p>Paste a GitHub URL to start the AI repair loop.</p>
              
              <div className="input-group">
                <input 
                  type="text" 
                  placeholder="https://github.com/user/repo" 
                  className="glass-input repo-input"
                  value={repoUrl}
                  onChange={(e) => setRepoUrl(e.target.value)}
                  disabled={isAnalyzing}
                />
                <button 
                  onClick={handleAnalyze} 
                  disabled={isAnalyzing || !repoUrl}
                  className={`glow-button ${isAnalyzing ? 'pulsing' : ''}`}
                >
                  {isAnalyzing ? 'Analyzing...' : 'Analyze & Repair'}
                </button>
              </div>
              {error && <div className="error-notification">❌ {error}</div>}
            </section>

            <div className="dashboard-grid">
              <section className="glass-panel terminal-section">
                <div className="terminal-header">
                  <div className="dots">
                    <span className="dot red"></span>
                    <span className="dot yellow"></span>
                    <span className="dot green"></span>
                  </div>
                  <div className="terminal-title">Agent Logs</div>
                  {isAnalyzing && <div className="live-indicator pulsing">● LIVE</div>}
                </div>
                <div className="terminal-body" ref={terminalRef}>
                  {logs.length === 0 && !isAnalyzing && (
                    <div className="terminal-placeholder">
                      <p>{">"} Waiting for repository input...</p>
                      <p className="dim text-sm">{">"} Ready to generate & fix unit tests automatically.</p>
                    </div>
                  )}
                  {logs.map((log, i) => (
                    <div key={i} className="log-line" dangerouslySetInnerHTML={{ __html: log }} />
                  ))}
                </div>
              </section>

              {report && (
                <section className="glass-panel report-section animate-fade-in">
                  <div className="report-header">
                    <h3>Analysis Complete</h3>
                    <div className={`status-badge ${report.success ? 'success' : 'failed'}`}>
                      {report.success ? 'SUCCESS' : 'FAILURE'}
                    </div>
                  </div>
                  
                  <div className="metrics-grid">
                    <div className="metric-card">
                      <div className="metric-label">Code Coverage</div>
                      <div className="metric-value">{report.coverage}</div>
                    </div>
                    <div className="metric-card">
                      <div className="metric-label">Repair Quality</div>
                      <div className="metric-value">Verified</div>
                    </div>
                  </div>

                  <div className="code-block">
                    <div className="code-header">Generated Tests</div>
                    <pre><code>{report.test_code}</code></pre>
                  </div>
                </section>
              )}
            </div>
          </div>
        ) : (
          <div className="history-view glass-panel animate-fade-in-up">
            <header className="history-header">
              <h2>Activity History</h2>
              <button className="refresh-btn" onClick={fetchHistory}>Refresh</button>
            </header>
            <div className="history-list">
              {history.length === 0 ? (
                <div className="empty-history">No past analyses found in your workspace.</div>
              ) : (
                <div className="history-grid">
                  {history.map((task) => (
                    <div key={task.id} className="history-card glass-panel-inner">
                      <div className="card-top">
                        <span className="card-date">{new Date(task.created_at).toLocaleDateString()}</span>
                        <span className={`card-status ${task.status}`}>{task.status.toUpperCase()}</span>
                      </div>
                      <div className="card-repo">{task.repo_url}</div>
                      <div className="card-metrics">
                        <span>Coverage: {task.coverage}</span>
                      </div>
                      <button 
                        className="card-view-btn"
                        onClick={() => {
                          setReport({
                            success: task.status === 'completed',
                            coverage: task.coverage,
                            test_code: task.test_code
                          });
                          setActiveTab('analyze');
                        }}
                      >
                        View Results
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
