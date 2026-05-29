export function mapStockResponse(data) {
  if (!data) return null
  return {
    ...data,
    metrics: mapMetrics(data.metrics),
  }
}

const priceFormat = new Intl.NumberFormat('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
const pctFormat = new Intl.NumberFormat('en-US', { style: 'percent', minimumFractionDigits: 1, maximumFractionDigits: 1, signDisplay: 'exceptZero' })
const capFormat = new Intl.NumberFormat('en-US', { minimumFractionDigits: 1, maximumFractionDigits: 1 })

function mapMetrics(m) {
  if (!m) return {}
  return {
    ...m,
    revenueGrowthDisplay: m.revenueGrowth != null
      ? pctFormat.format(m.revenueGrowth)
      : '--',
    marketCapDisplay: formatMarketCap(m.marketCap),
  }
}

function formatMarketCap(cap) {
  if (!cap) return '--'
  if (cap >= 1e12) return capFormat.format(cap / 1e12) + 'T'
  if (cap >= 1e9) return capFormat.format(cap / 1e9) + 'B'
  if (cap >= 1e6) return capFormat.format(cap / 1e6) + 'M'
  return priceFormat.format(cap)
}

export function toErrorMessage(error) {
  if (!error) return 'Unknown error'
  if (error.name === 'AbortError') return ''
  if (error.message.includes('404')) return 'No data found for this ticker'
  if (error.message.includes('429')) return 'Too many requests. Please wait a moment.'
  if (error.message.includes('400')) return 'Invalid ticker format'
  return error.message || 'Something went wrong'
}
