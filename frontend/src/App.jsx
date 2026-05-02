import { useState } from 'react'
import './App.css'

const inferredApiBaseUrl =
  window.location.hostname === 'amp-front.acutistecnologia.com'
    ? 'https://amp-back.acutistecnologia.com'
    : 'http://localhost:8002'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || inferredApiBaseUrl

function IconSpark() {
  return <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2l1.7 5.3L19 9l-5.3 1.7L12 16l-1.7-5.3L5 9l5.3-1.7L12 2z" /></svg>
}

function IconScale() {
  return <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 7h16M7 7l-3 6h6l-3-6zm10 0l-3 6h6l-3-6zM12 4v15m-5 1h10" /></svg>
}

function IconShield() {
  return <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3l7 3v5c0 5-3.2 8.1-7 10-3.8-1.9-7-5-7-10V6l7-3zm-3.2 8.5l2.2 2.2 4.2-4.2" /></svg>
}

function IconFile() {
  return <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 3h7l5 5v13H7V3zm7 1v5h5" /></svg>
}

function App() {
  const [report, setReport] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [showJson, setShowJson] = useState(false)
  const [statusFilter, setStatusFilter] = useState('all')
  const [severityFilter, setSeverityFilter] = useState('all')

  const runAnalysis = async () => {
    setLoading(true)
    setError(null)
    setReport(null)

    try {
      const response = await fetch(`${API_BASE_URL}/analyze`, {
        method: 'POST',
      })

      if (!response.ok) {
        throw new Error(`Server responded with ${response.status}`)
      }

      const data = await response.json()
      setReport(data.report)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const filteredFindings = report
    ? report.findings.filter((finding) => {
        const statusMatch = statusFilter === 'all' || finding.status === statusFilter
        const severityMatch = severityFilter === 'all' || finding.severity === severityFilter
        return statusMatch && severityMatch
      })
    : []

  const citationRows = report
    ? report.citations.map((citation) => {
        const verification = report.citation_verifications.find((item) => item.citation_id === citation.id)
        return {
          id: citation.id,
          citation: citation.citation,
          type: citation.citation_type,
          support_level: verification?.support_level || 'n/a',
          supports_claim: verification?.supports_claim,
          confidence: verification?.confidence,
        }
      })
    : []

  return (
    <div className="app-shell">
      <div className="ambient" aria-hidden="true" />
      <main className="page">
        <section className="hero">
          <p className="eyebrow">Case Review System</p>
          <h1>BS Detector</h1>
          <p className="subtitle">Structured legal-brief verification with citation checks, quote fidelity, and cross-document consistency.</p>
          <div className="hero-actions">
            <button className="primary" onClick={runAnalysis} disabled={loading}>
              {loading ? 'Analyzing Records...' : 'Run Analysis'}
            </button>
            <button className="ghost" onClick={() => setShowJson((v) => !v)} disabled={!report}>
              {showJson ? 'Hide JSON' : 'Show JSON'}
            </button>
          </div>
        </section>

        {error && <div className="error">Error: {error}</div>}

        {loading && (
          <section className="grid metrics">
            {[1, 2, 3, 4].map((item) => (
              <div key={item} className="skeleton-card">
                <div className="skeleton-line short" />
                <div className="skeleton-line" />
              </div>
            ))}
          </section>
        )}

        {!loading && report && (
          <>
            <section className="grid metrics stagger-group">
              <article className="metric-card stagger-item">
                <div className="icon"><IconFile /></div>
                <p>Total findings</p>
                <h3>{report.summary.total_findings}</h3>
              </article>
              <article className="metric-card stagger-item">
                <div className="icon"><IconSpark /></div>
                <p>High confidence</p>
                <h3>{report.summary.high_confidence_findings}</h3>
              </article>
              <article className="metric-card stagger-item">
                <div className="icon"><IconScale /></div>
                <p>Medium confidence</p>
                <h3>{report.summary.medium_confidence_findings}</h3>
              </article>
              <article className="metric-card stagger-item">
                <div className="icon"><IconShield /></div>
                <p>Could not verify</p>
                <h3>{report.summary.could_not_verify}</h3>
              </article>
            </section>

            <section className="content-grid stagger-group">
              <article className="panel memo stagger-item">
                <h2>Judicial memo</h2>
                <p>{report.judicial_memo}</p>
              </article>

              <article className="panel findings stagger-item">
                <h2>Findings</h2>
                <div className="filters">
                  <label>
                    Status
                    <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
                      <option value="all">All</option>
                      <option value="verified_issue">verified_issue</option>
                      <option value="could_not_verify">could_not_verify</option>
                      <option value="no_issue">no_issue</option>
                    </select>
                  </label>
                  <label>
                    Severity
                    <select value={severityFilter} onChange={(event) => setSeverityFilter(event.target.value)}>
                      <option value="all">All</option>
                      <option value="high">high</option>
                      <option value="medium">medium</option>
                      <option value="low">low</option>
                    </select>
                  </label>
                </div>
                {filteredFindings.map((finding) => (
                  <div key={finding.id} className="finding-row">
                    <div className="row-top">
                      <strong>{finding.type.replaceAll('_', ' ')}</strong>
                      <span className={`pill ${finding.status}`}>{finding.status.replaceAll('_', ' ')}</span>
                    </div>
                    <p className="assessment">{finding.assessment}</p>
                    <p className="meta">Severity {finding.severity} · confidence {finding.confidence}</p>
                    {finding.evidence && <p className="meta">Source: {finding.evidence.source_document}</p>}
                  </div>
                ))}
                {filteredFindings.length === 0 && <p className="empty-inline">No findings match the selected filters.</p>}
              </article>
            </section>

            <section className="panel table-panel stagger-group">
              <h2>Citations and verification</h2>
              <div className="table-wrap stagger-item">
                <table>
                  <thead>
                    <tr>
                      <th>ID</th>
                      <th>Citation</th>
                      <th>Type</th>
                      <th>Support level</th>
                      <th>Supports claim</th>
                      <th>Confidence</th>
                    </tr>
                  </thead>
                  <tbody>
                    {citationRows.map((row) => (
                      <tr key={row.id}>
                        <td>{row.id}</td>
                        <td className="citation-cell">{row.citation}</td>
                        <td>{row.type}</td>
                        <td>{row.support_level}</td>
                        <td>{String(row.supports_claim)}</td>
                        <td>{row.confidence !== undefined ? row.confidence : 'n/a'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>

            {showJson && (
              <section className="panel json stagger-group">
                <h2>Raw JSON</h2>
                <pre className="stagger-item">{JSON.stringify(report, null, 2)}</pre>
              </section>
            )}
          </>
        )}

        {report === null && !loading && !error && <p className="empty">Run analysis to generate the verification report.</p>}
      </main>
    </div>
  )
}

export default App
