<template>
  <div class="app">
    <header>
      <h1>AI Bubble Detector</h1>
      <p class="subtitle">Detect overvaluation signals in AI-related stocks</p>
    </header>
    <StockAnalyzer />
  </div>
</template>

<script setup>
import StockAnalyzer from './components/StockAnalyzer.vue'
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
  background: #0f172a;
  color: #e2e8f0;
  min-height: 100vh;
}

.app {
  max-width: 800px;
  margin: 0 auto;
  padding: 2rem 1rem;
}

header {
  text-align: center;
  margin-bottom: 2rem;
}

h1 {
  font-size: 2rem;
  background: linear-gradient(135deg, #a78bfa, #60a5fa);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.subtitle {
  color: #94a3b8;
  margin-top: 0.25rem;
}
</style>
