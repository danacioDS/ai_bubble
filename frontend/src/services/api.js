const API_BASE =
  (window.__APP_CONFIG__ && window.__APP_CONFIG__.apiUrl) ||
  import.meta.env.VITE_API_URL ||
  'http://localhost:8000'

export async function fetchStockData(ticker, { signal } = {}) {
  const res = await fetch(`${API_BASE}/stock/${ticker}`, { signal })
  if (!res.ok) throw new Error(`API error: ${res.status}`)
  return res.json()
}

export async function fetchStockHistory(ticker, { signal } = {}) {
  const res = await fetch(`${API_BASE}/stock/${ticker}/history`, { signal })
  if (!res.ok) throw new Error(`History API error: ${res.status}`)
  return res.json()
}
