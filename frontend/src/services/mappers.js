export function mapStockResponse(data) {
  if (!data) return null
  return {
    ...data,
    metrics: mapMetrics(data.metrics),
  }
}

function mapMetrics(m) {
  if (!m) return {}
  return {
    ...m,
    revenueGrowthDisplay: m.revenueGrowth != null
      ? (m.revenueGrowth * 100).toFixed(1) + '%'
      : '--',
    marketCapDisplay: formatMarketCap(m.marketCap),
  }
}

function formatMarketCap(cap) {
  if (!cap) return '--'
  if (cap >= 1e12) return (cap / 1e12).toFixed(2) + 'T'
  if (cap >= 1e9) return (cap / 1e9).toFixed(2) + 'B'
  if (cap >= 1e6) return (cap / 1e6).toFixed(2) + 'M'
  return cap
}

export function toErrorMessage(error) {
  if (!error) return 'Unknown error'
  if (error.name === 'AbortError') return ''
  if (error.message.includes('404')) return 'No data found for this ticker'
  if (error.message.includes('429')) return 'Too many requests. Please wait a moment.'
  if (error.message.includes('400')) return 'Invalid ticker format'
  return error.message || 'Something went wrong'
}
