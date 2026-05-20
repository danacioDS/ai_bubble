<template>
  <div class="analyzer">
    <div class="search-box">
      <input
        v-model="ticker"
        class="input"
        placeholder="Enter ticker (e.g. NVDA, AAPL, MSFT)"
        @keyup.enter="analyze"
      />
      <button class="btn" :disabled="loading" @click="analyze">
        {{ loading ? 'Loading...' : 'Analyze' }}
      </button>
    </div>

    <div v-if="error" class="error">{{ error }}</div>

    <div v-if="data" class="card">
      <div class="card-header">
        <div>
          <h2>{{ data.name || data.ticker }}</h2>
          <span class="ticker-badge">{{ data.ticker }}</span>
        </div>
        <div class="score-ring" :class="scoreClass">
          <svg viewBox="0 0 36 36" class="ring-svg">
            <path
              class="ring-bg"
              d="M18 2.0845
                a 15.9155 15.9155 0 0 1 0 31.831
                a 15.9155 15.9155 0 0 1 0 -31.831"
            />
            <path
              class="ring-fill"
              :stroke-dasharray="scorePercent + ', 100'"
              d="M18 2.0845
                a 15.9155 15.9155 0 0 1 0 31.831
                a 15.9155 15.9155 0 0 1 0 -31.831"
            />
            <text x="18" y="20.5" class="ring-text">{{ data.score }}</text>
          </svg>
          <div class="score-label">{{ scoreLabel }}</div>
        </div>
      </div>

      <div class="metrics">
        <div class="metric">
          <span class="metric-label">Price</span>
          <span class="metric-value">${{ data.price }}</span>
        </div>
        <div class="metric">
          <span class="metric-label">P/E</span>
          <span class="metric-value" :class="{ warn: data.metrics.pe > 30 }">{{ data.metrics.pe ?? '--' }}</span>
        </div>
        <div class="metric">
          <span class="metric-label">Forward P/E</span>
          <span class="metric-value">{{ data.metrics.forwardPe ?? '--' }}</span>
        </div>
        <div class="metric">
          <span class="metric-label">Rev. Growth</span>
          <span class="metric-value" :class="{ warn: data.metrics.revenueGrowth > 0.3 }">
            {{ data.metrics.revenueGrowth != null ? (data.metrics.revenueGrowth * 100).toFixed(1) + '%' : '--' }}
          </span>
        </div>
        <div class="metric">
          <span class="metric-label">P/B</span>
          <span class="metric-value" :class="{ warn: data.metrics.priceToBook > 10 }">
            {{ data.metrics.priceToBook ?? '--' }}
          </span>
        </div>
        <div class="metric">
          <span class="metric-label">Market Cap</span>
          <span class="metric-value">{{ formatMarketCap(data.metrics.marketCap) }}</span>
        </div>
      </div>

      <div v-if="data.reasons && data.reasons.length" class="reasons">
        <h3>Bubble Signals</h3>
        <ul>
          <li v-for="r in data.reasons" :key="r">{{ r }}</li>
        </ul>
      </div>

      <div v-if="prices.length" class="chart-wrapper">
        <h3>Price History (6 months)</h3>
        <svg
          :viewBox="`0 0 ${chartW} ${chartH}`"
          class="chart-svg"
          preserveAspectRatio="none"
        >
          <polyline
            :points="chartPoints"
            fill="none"
            stroke="#a78bfa"
            stroke-width="2"
          />
        </svg>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

let currentController = null

const ticker = ref('')
const data = ref(null)
const prices = ref([])
const loading = ref(false)
const error = ref('')

const chartW = 600
const chartH = 200

const scorePercent = computed(() => {
  if (!data.value) return 0
  return Math.min((data.value.score / 9) * 100, 100)
})

const scoreClass = computed(() => {
  if (!data.value) return ''
  const s = data.value.score
  if (s >= 6) return 'danger'
  if (s >= 4) return 'warning'
  return 'safe'
})

const scoreLabel = computed(() => {
  if (!data.value) return ''
  const s = data.value.score
  if (s >= 6) return 'High Bubble Risk'
  if (s >= 4) return 'Moderate Risk'
  return 'Low Risk'
})

const chartPoints = computed(() => {
  if (!prices.value.length) return ''
  const min = Math.min(...prices.value.map(p => p.close))
  const max = Math.max(...prices.value.map(p => p.close))
  const range = max - min || 1
  const pad = 10

  return prices.value
    .map((p, i) => {
      const x = pad + (i / (prices.value.length - 1)) * (chartW - 2 * pad)
      const y = chartH - pad - ((p.close - min) / range) * (chartH - 2 * pad)
      return `${x},${y}`
    })
    .join(' ')
})

async function analyze() {
  if (!ticker.value.trim()) return

  if (currentController) {
    currentController.abort()
  }
  currentController = new AbortController()
  const { signal } = currentController

  loading.value = true
  error.value = ''
  data.value = null
  prices.value = []

  try {
    const [stockRes, histRes] = await Promise.all([
      fetch(`${API_BASE}/stock/${ticker.value}`, { signal }),
      fetch(`${API_BASE}/stock/${ticker.value}/history`, { signal }),
    ])

    if (!stockRes.ok) {
      throw new Error(`API error: ${stockRes.status}`)
    }
    if (!histRes.ok) {
      throw new Error(`History API error: ${histRes.status}`)
    }

    data.value = await stockRes.json()
    const histData = await histRes.json()
    prices.value = histData.prices || []
  } catch (e) {
    if (e.name === 'AbortError') return
    error.value = e.message
  } finally {
    loading.value = false
  }
}

function formatMarketCap(cap) {
  if (!cap) return '--'
  if (cap >= 1e12) return (cap / 1e12).toFixed(2) + 'T'
  if (cap >= 1e9) return (cap / 1e9).toFixed(2) + 'B'
  if (cap >= 1e6) return (cap / 1e6).toFixed(2) + 'M'
  return cap
}
</script>

<style scoped>
.search-box {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
}

.input {
  flex: 1;
  padding: 0.75rem 1rem;
  border: 1px solid #334155;
  border-radius: 8px;
  background: #1e293b;
  color: #e2e8f0;
  font-size: 1rem;
  outline: none;
  transition: border-color 0.2s;
}

.input:focus {
  border-color: #a78bfa;
}

.btn {
  padding: 0.75rem 1.5rem;
  background: #7c3aed;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  cursor: pointer;
  transition: background 0.2s;
}

.btn:hover:not(:disabled) {
  background: #6d28d9;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.error {
  background: #7f1d1d;
  color: #fca5a5;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  margin-bottom: 1rem;
}

.card {
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 12px;
  padding: 1.5rem;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1.5rem;
}

.card-header h2 {
  font-size: 1.5rem;
  margin-bottom: 0.25rem;
}

.ticker-badge {
  display: inline-block;
  background: #334155;
  padding: 0.15rem 0.6rem;
  border-radius: 4px;
  font-size: 0.8rem;
  color: #94a3b8;
}

.score-ring {
  text-align: center;
}

.ring-svg {
  width: 60px;
  height: 60px;
  transform: rotate(-90deg);
}

.ring-bg {
  fill: none;
  stroke: #334155;
  stroke-width: 3;
}

.ring-fill {
  fill: none;
  stroke-width: 3;
  stroke-linecap: round;
  transition: stroke-dasharray 0.5s;
}

.safe .ring-fill { stroke: #22c55e; }
.warning .ring-fill { stroke: #eab308; }
.danger .ring-fill { stroke: #ef4444; }

.ring-text {
  transform: rotate(90deg);
  transform-origin: 18px 18px;
  fill: #e2e8f0;
  font-size: 8px;
  text-anchor: middle;
  font-weight: bold;
}

.score-label {
  font-size: 0.7rem;
  margin-top: 0.25rem;
  color: #94a3b8;
}

.metrics {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.metric {
  background: #0f172a;
  padding: 0.75rem;
  border-radius: 8px;
}

.metric-label {
  display: block;
  font-size: 0.75rem;
  color: #94a3b8;
  margin-bottom: 0.25rem;
}

.metric-value {
  font-size: 1.125rem;
  font-weight: 600;
}

.metric-value.warn {
  color: #eab308;
}

.reasons {
  margin-bottom: 1.5rem;
}

.reasons h3 {
  font-size: 1rem;
  margin-bottom: 0.5rem;
  color: #fbbf24;
}

.reasons ul {
  list-style: none;
}

.reasons li {
  padding: 0.35rem 0.75rem;
  background: #0f172a;
  border-left: 3px solid #a78bfa;
  border-radius: 4px;
  margin-bottom: 0.35rem;
  font-size: 0.9rem;
  color: #cbd5e1;
}

.chart-wrapper h3 {
  font-size: 1rem;
  margin-bottom: 0.75rem;
}

.chart-svg {
  width: 100%;
  height: 200px;
  background: #0f172a;
  border-radius: 8px;
}
</style>
