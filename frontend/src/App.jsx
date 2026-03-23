import { useState, useRef, useEffect } from 'react'

function App() {
  const [repoUrl, setRepoUrl] = useState('')
  const [taskId, setTaskId] = useState(null)
  const [logs, setLogs] = useState([])
  const [report, setReport] = useState(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const terminalEndRef = useRef(null)

  useEffect(() => {
    terminalEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [logs])

  const handleAnalyze = async (e) => {
    e.preventDefault()
    if (!repoUrl) return
    
    setIsAnalyzing(true)
    setLogs([])
    setReport(null)
    setTaskId(null)

    try {
      const res = await fetch('http://localhost:8001/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ repo_url: repoUrl })
      })
      const data = await res.json()
      setTaskId(data.task_id)
    } catch (err) {
      setLogs(prev => [...prev, `❌ Error: ${err.message}`])
      setIsAnalyzing(false)
    }
  }

  useEffect(() => {
    if (!taskId) return

    const eventSource = new EventSource(`http://localhost:8001/api/stream/${taskId}`)
    
    eventSource.onmessage = (event) => {
      const rawData = event.data
      
      if (rawData.startsWith("[REPORT]")) {
        try {
          const reportJsonStr = rawData.substring(8).replace(/<br>/g, '\\n')
          const reportData = JSON.parse(reportJsonStr)
          setReport(reportData)
        } catch (e) {
          console.error("Failed to parse report data", e)
        }
        return
      }

      const formattedLog = rawData.replace(/<br>/g, '\\n')
      setLogs(prev => [...prev, formattedLog])
      
      if (rawData === "[DONE]" || formattedLog.includes("Analysis complete!") || formattedLog.includes("Terminating")) {
        eventSource.close()
        setIsAnalyzing(false)
        return
      }
    }

    eventSource.onerror = (err) => {
      console.error('SSE Error:', err)
      eventSource.close()
      setIsAnalyzing(false)
      setLogs(prev => [...prev, '❌ Connection to agent lost.'])
    }

    return () => {
      eventSource.close()
    }
  }, [taskId])

  return (
    <div className="app-container">
      <div className="background-shapes">
        <div className="shape shape-1"></div>
        <div className="shape shape-2"></div>
      </div>
      
      <main className="main-content glass-panel">
        <header className="header">
          <h1 className="title">
            <span className="gradient-text">Autonomous</span> Test Agent
          </h1>
          <p className="subtitle">AI-driven testing for real-world repositories</p>
        </header>

        <form className="input-group" onSubmit={handleAnalyze}>
          <input 
            type="url" 
            placeholder="https://github.com/username/repository"
            value={repoUrl}
            onChange={(e) => setRepoUrl(e.target.value)}
            disabled={isAnalyzing}
            className="repo-input glass-input"
            required
          />
          <button 
            type="submit" 
            className={`glow-button ${isAnalyzing ? 'pulsing' : ''}`}
            disabled={isAnalyzing}
          >
            {isAnalyzing ? 'Analyzing...' : 'Analyze Repo'}
          </button>
        </form>

        <div className="terminal-container glass-panel-inner">
          <div className="terminal-header">
            <div className="dots">
              <span className="dot red"></span>
              <span className="dot yellow"></span>
              <span className="dot green"></span>
            </div>
            <span className="terminal-title">agent_execution.log</span>
          </div>
          <div className="terminal-body" style={{ height: report ? '200px' : '400px', transition: 'height 0.3s' }}>
            {logs.length === 0 && !isAnalyzing ? (
              <p className="terminal-placeholder">Awaiting repository URL to begin initial analysis...</p>
            ) : (
              logs.map((log, i) => (
                <div key={i} className="log-line">
                  {log.split('\\n').map((line, j) => (
                    <span key={j} className="log-segment">{line}<br/></span>
                  ))}
                </div>
              ))
            )}
            <div ref={terminalEndRef} />
          </div>
        </div>

        {report && (
          <div className="report-panel glass-panel-inner animate-fade-in">
            <div className="report-header">
              <h2 className="report-title">Automated Test Report</h2>
              <div className="badge">Generated Successfully</div>
            </div>
            
            <div className="report-stats">
              <div className="stat-card">
                <span className="stat-label">Test Coverage</span>
                <span className="stat-value gradient-text">{report.coverage}</span>
              </div>
              <div className="stat-card">
                <span className="stat-label">Execution Status</span>
                <span className={`stat-value ${report.success ? 'text-green' : 'text-red'}`}>
                  {report.success ? 'Pass' : 'Fail'}
                </span>
              </div>
            </div>
            
            <h3 className="code-title">Generated Unit Tests</h3>
            <div className="code-container">
              <pre className="code-block">
                <code>{report.test_code || 'No tests generated.'}</code>
              </pre>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}

export default App
