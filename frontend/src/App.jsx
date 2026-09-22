import { useEffect, useMemo, useRef, useState } from 'react'

const API_PREFIX = '/api'

async function readResponse(response) {
  const payload = await response.json().catch(() => ({}))
  if (!response.ok) throw new Error(payload.detail || 'The request could not be completed.')
  return payload
}

function formatConfidence(value) {
  return `${Math.round(value || 0)}%`
}

function App() {
  const historicalInput = useRef(null)
  const predictionInput = useRef(null)
  const [activeView, setActiveView] = useState('workspace')
  const [historicalFiles, setHistoricalFiles] = useState([])
  const [predictionFile, setPredictionFile] = useState(null)
  const [history, setHistory] = useState(null)
  const [result, setResult] = useState(null)
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState({ type: '', message: '' })
  const [busy, setBusy] = useState('')

  const loadHistory = async () => {
    try {
      const response = await fetch(`${API_PREFIX}/history`)
      setHistory(await readResponse(response))
    } catch {
      setHistory(null)
    }
  }

  useEffect(() => { loadHistory() }, [])

  const visiblePredictions = useMemo(() => {
    if (!result?.predictions) return []
    const query = search.trim().toLowerCase()
    if (!query) return result.predictions
    return result.predictions.filter((prediction) =>
      [prediction.location, prediction.day, prediction.shift_type, prediction.assigned_person]
        .filter(Boolean).some((value) => value.toLowerCase().includes(query)),
    )
  }, [result, search])

  const uploadHistorical = async () => {
    if (!historicalFiles.length) return
    setBusy('history'); setStatus({ type: '', message: '' })
    try {
      const formData = new FormData()
      historicalFiles.forEach((file) => formData.append('files', file))
      const response = await fetch(`${API_PREFIX}/upload-historical`, { method: 'POST', body: formData })
      const payload = await readResponse(response)
      setStatus({ type: 'success', message: `${payload.total_records_added} historical shifts added to the learning set.` })
      setHistoricalFiles([])
      if (historicalInput.current) historicalInput.current.value = ''
      await loadHistory()
    } catch (error) { setStatus({ type: 'error', message: error.message }) }
    finally { setBusy('') }
  }

  const generatePredictions = async () => {
    if (!predictionFile) return
    setBusy('prediction'); setStatus({ type: '', message: '' })
    try {
      const formData = new FormData(); formData.append('file', predictionFile)
      const response = await fetch(`${API_PREFIX}/predict`, { method: 'POST', body: formData })
      const payload = await readResponse(response)
      setResult(payload); setActiveView('workspace')
      setStatus({ type: 'success', message: 'Prediction run complete. Review flagged shifts before publishing.' })
    } catch (error) { setStatus({ type: 'error', message: error.message }) }
    finally { setBusy('') }
  }

  const clearRun = () => {
    setResult(null); setPredictionFile(null); setSearch('')
    if (predictionInput.current) predictionInput.current.value = ''
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand"><span className="brand-mark">S</span><span>shift<span className="brand-accent">sense</span></span></div>
        <div className="sidebar-label">Workspace</div>
        <nav className="nav-list" aria-label="Main navigation">
          <button className={`nav-item ${activeView === 'history' ? 'active' : ''}`} onClick={() => setActiveView('history')}><span className="nav-icon">◌</span> Learning history</button>
        </nav>
        <div className="sidebar-bottom"><div className="model-status"><span className="status-dot" /> System ready</div></div>
      </aside>

      <main className="main-content">
        {activeView === 'history' && <header className="topbar"><div><p className="eyebrow">Learning history</p><h1>Historical data</h1></div></header>}
        {status.message && <div className={`notice ${status.type}`} role="status">{status.message}</div>}

        {activeView === 'history' ? (
          <section className="history-view"><div className="section-heading"><div><p className="eyebrow">Model context</p><h2>Historical coverage</h2></div><div className="section-actions"><button className="connection-button" type="button"><span className="status-dot" /> Connected</button><span className="pill">Live from API</span></div></div><div className="history-upload workflow-card"><div className="card-number">01 <span>Learning set</span></div><h3>Upload completed weeks</h3><p className="card-help">Add one or more `.xlsx` workbooks with names in the Notes column.</p><FileDrop files={historicalFiles} inputRef={historicalInput} multiple onChange={(event) => setHistoricalFiles(Array.from(event.target.files || []))} /><button className="button primary" disabled={!historicalFiles.length || busy === 'history'} onClick={uploadHistorical}>{busy === 'history' ? 'Processing...' : 'Add to learning set'} <span>→</span></button></div><div className="metric-grid"><Metric label="Shifts learned" value={history?.total_historical_shifts ?? '—'} accent="teal" /><Metric label="Weeks represented" value={history?.weeks_of_data ?? '—'} accent="yellow" /><Metric label="AI reasoning" value={history?.ai_reasoning_available ? 'Ready' : 'Fallback'} accent="coral" /></div><div className="history-panel"><div><h3>Week breakdown</h3><p>Recent uploads currently held by the in-memory pattern engine.</p></div>{history?.week_breakdown?.length ? history.week_breakdown.map((week) => <div className="week-row" key={week.week_offset}><span>Week offset {week.week_offset}</span><strong>{week.shift_count} shifts</strong><div className="bar"><i style={{ width: `${Math.min(100, week.shift_count * 5)}%` }} /></div></div>) : <div className="empty-state">No historical workbooks have been uploaded yet.</div>}</div></section>
        ) : (
          <><section className="hero-grid"><div className="hero-copy"><h2>Schedule with confidence.</h2><p>Upload completed schedules to learn your patterns, then generate the next week in one step.</p></div></section>
            <section className="workflow-grid"><article className="workflow-card prediction-card"><div className="card-number">01 <span>New schedule</span></div><h3>Generate allocations</h3><p className="card-help">Choose a blank week and get suggested assignments in seconds.</p><FileDrop files={predictionFile ? [predictionFile] : []} inputRef={predictionInput} onChange={(event) => setPredictionFile(event.target.files?.[0] || null)} /><button className="button primary" disabled={!predictionFile || busy === 'prediction'} onClick={generatePredictions}>{busy === 'prediction' ? 'Analysing...' : 'Generate predictions'} <span>↗</span></button></article></section>
            <section className="results-section"><div className="section-heading"><div><p className="eyebrow">Review queue</p><h2>{result ? 'Proposed assignments' : 'No run yet'}</h2></div>{result && <button className="text-button" onClick={clearRun}>Clear run</button>}</div>{result ? <><div className="metric-grid compact"><Metric label="Total shifts" value={result.summary.total_shifts} accent="teal" /><Metric label="Confident" value={result.summary.confident_predictions} accent="yellow" /><Metric label="Needs review" value={result.summary.flagged_for_review} accent="coral" /><Metric label="Conflicts resolved" value={result.summary.conflicts_resolved} accent="ink" /></div><div className="table-toolbar"><div className="search-wrap"><span>⌕</span><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search location, day or person" /></div><a className="download-link" href={`${API_PREFIX}${result.download_url}`} download>Download workbook ↗</a></div><PredictionTable predictions={visiblePredictions} /></> : <div className="empty-state large">Your generated assignments will appear here for a quick review before download.</div>}</section>
          </>
        )}
      </main>
    </div>
  )
}

function Metric({ label, value, accent }) { return <div className={`metric metric-${accent}`}><span>{label}</span><strong>{value}</strong></div> }
function FileDrop({ files, inputRef, multiple = false, onChange }) { return <label className="file-drop"><input ref={inputRef} type="file" accept=".xlsx" multiple={multiple} onChange={onChange} /><span className="upload-symbol">＋</span><span>{files.length ? `${files.length} workbook${files.length === 1 ? '' : 's'} selected` : 'Choose .xlsx workbook'}</span><small>{files.length ? files.map((file) => file.name).join(', ') : 'or drop it here'}</small></label> }
function PredictionTable({ predictions }) { if (!predictions.length) return <div className="empty-state">No shifts match your search.</div>; return <div className="table-wrap"><table><thead><tr><th>Shift</th><th>Assignment</th><th>Confidence</th><th>Status</th><th>Reasoning</th></tr></thead><tbody>{predictions.map((prediction, index) => <tr key={`${prediction.date}-${prediction.location}-${index}`}><td><strong>{prediction.location}</strong><span>{prediction.day} · {prediction.shift_type} · {prediction.start_time}–{prediction.end_time}</span></td><td className="assignment">{prediction.assigned_person || 'Unassigned'}</td><td><span className={`confidence ${prediction.confidence >= 80 ? 'high' : prediction.confidence >= 60 ? 'medium' : 'low'}`}>{formatConfidence(prediction.confidence)}</span></td><td><span className={`status-badge ${prediction.needs_review ? 'review' : 'ready'}`}>{prediction.needs_review ? 'Review' : 'Ready'}</span></td><td className="reasoning">{prediction.reasoning || 'No reasoning available.'}</td></tr>)}</tbody></table></div> }

export default App