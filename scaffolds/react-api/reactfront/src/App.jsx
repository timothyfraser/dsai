import { useEffect, useState } from 'react'
import { API_URL, checkApi, parseValues, summarizeOnServer } from './api.js'

export default function App() {
  const [text, setText] = useState('1, 2, 3, 4, 5')
  const [api, setApi] = useState({ state: 'checking' })
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    checkApi()
      .then((r) => setApi({ state: 'ok', version: r.version }))
      .catch(() => setApi({ state: 'down' }))
  }, [])

  async function run() {
    setError('')
    setResult(null)
    try {
      setResult(await summarizeOnServer(parseValues(text)))
    } catch (e) {
      setError(e.message)
    }
  }

  return (
    <main>
      <h1>React page over an API</h1>
      <p className={`api ${api.state}`} role="status">
        API at <code>{API_URL}</code>:{' '}
        {api.state === 'checking' && 'checking...'}
        {api.state === 'ok' && `connected (version ${api.version})`}
        {api.state === 'down' && 'not reachable. Is the API running?'}
      </p>

      <label htmlFor="values">Numbers (comma or space separated)</label>
      <textarea id="values" rows={3} value={text} onChange={(e) => setText(e.target.value)} />
      <button onClick={run} disabled={api.state !== 'ok'}>Summarize on the API</button>

      {error && <p className="error" role="alert">{error}</p>}
      {result && (
        <dl className="stats">
          <div><dt>Count</dt><dd>{result.n}</dd></div>
          <div><dt>Mean</dt><dd>{result.mean}</dd></div>
          <div><dt>Min</dt><dd>{result.min}</dd></div>
          <div><dt>Max</dt><dd>{result.max}</dd></div>
        </dl>
      )}
    </main>
  )
}
