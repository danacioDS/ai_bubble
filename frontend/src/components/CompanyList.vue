<template>
  <div class="company-list">
    <div class="search-bar">
      <input
        v-model="searchQuery"
        class="search-input"
        placeholder="Search ticker or company..."
      />
    </div>

    <div
      v-for="sector in filteredSectors"
      :key="sector.name"
      class="sector-group"
    >
      <button class="sector-header" @click="toggleSector(sector.name)">
        <span class="sector-icon">{{ sector.icon }}</span>
        <span class="sector-name">{{ sector.name }}</span>
        <span class="sector-count">{{ sector.companies.length }}</span>
        <span class="chevron" :class="{ open: openSectors[sector.name] }">▸</span>
      </button>
      <div v-if="computedOpen[sector.name]" class="sector-companies">
        <button
          v-for="c in sector.companies"
          :key="c.ticker"
          class="company-btn"
          :class="{ active: selectedTicker === c.ticker }"
          @click="select(c.ticker)"
        >
          <span class="company-ticker">{{ c.ticker }}</span>
          <span class="company-name">{{ c.name }}</span>
        </button>
      </div>
    </div>

    <div v-if="filteredSectors.length === 0" class="no-results">
      No companies match "{{ searchQuery }}"
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import sectorsData from '../data/companies.json'

const emit = defineEmits(['select'])

const props = defineProps({
  selectedTicker: { type: String, default: '' },
})

const openSectors = reactive({})
const searchQuery = ref('')

const sectors = ref(sectorsData)

const filteredSectors = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return sectors.value

  return sectors.value
    .map(s => ({
      ...s,
      companies: s.companies.filter(c =>
        c.ticker.toLowerCase().includes(q) ||
        c.name.toLowerCase().includes(q)
      ),
    }))
    .filter(s => s.companies.length > 0)
})

// Auto-expand sectors when searching
const computedOpen = computed(() => {
  if (searchQuery.value.trim()) {
    const open = {}
    for (const s of filteredSectors.value) {
      open[s.name] = true
    }
    return open
  }
  return openSectors
})

function toggleSector(name) {
  openSectors[name] = !openSectors[name]
}

function select(ticker) {
  emit('select', ticker)
}
</script>

<style scoped>
.search-bar {
  margin-bottom: 0.75rem;
}

.search-input {
  width: 100%;
  padding: 0.6rem 0.75rem;
  border: 1px solid #334155;
  border-radius: 8px;
  background: #1e293b;
  color: #e2e8f0;
  font-size: 0.85rem;
  outline: none;
  transition: border-color 0.2s;
  box-sizing: border-box;
}

.search-input:focus {
  border-color: #a78bfa;
}

.search-input::placeholder {
  color: #64748b;
}

.company-list {
  margin-bottom: 1.5rem;
}

.sector-group {
  border: 1px solid #334155;
  border-radius: 8px;
  margin-bottom: 0.5rem;
  overflow: hidden;
}

.sector-header {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.65rem 1rem;
  background: #1e293b;
  border: none;
  color: #e2e8f0;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  text-align: left;
  transition: background 0.2s;
}

.sector-header:hover {
  background: #334155;
}

.sector-icon {
  font-size: 1rem;
}

.sector-name {
  flex: 1;
}

.sector-count {
  font-size: 0.75rem;
  color: #64748b;
  background: #0f172a;
  padding: 0.1rem 0.45rem;
  border-radius: 10px;
}

.chevron {
  font-size: 0.8rem;
  transition: transform 0.2s;
  color: #64748b;
}

.chevron.open {
  transform: rotate(90deg);
}

.sector-companies {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 0.25rem;
  padding: 0.5rem;
  background: #0f172a;
}

.company-btn {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.5rem 0.65rem;
  background: transparent;
  border: 1px solid transparent;
  border-radius: 6px;
  color: #cbd5e1;
  font-size: 0.8rem;
  cursor: pointer;
  text-align: left;
  transition: all 0.15s;
}

.company-btn:hover {
  background: #1e293b;
  border-color: #334155;
}

.company-btn.active {
  background: #1e1b4b;
  border-color: #a78bfa;
}

.company-ticker {
  font-weight: 700;
  color: #a78bfa;
  font-size: 0.85rem;
  min-width: 52px;
}

.company-name {
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.no-results {
  text-align: center;
  padding: 1.5rem;
  color: #64748b;
  font-size: 0.9rem;
}
</style>
