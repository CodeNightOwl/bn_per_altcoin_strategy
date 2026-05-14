<template>
  <div id="app">
    <nav class="nav">
      <div class="nav-inner">
        <router-link to="/coins" class="brand">
          <span class="brand-mark">◈</span>
          <span class="brand-text">山寨监控</span>
        </router-link>
        <div class="nav-links">
          <router-link to="/coins" class="nav-link" active-class="active">行情</router-link>
          <router-link to="/short-term" class="nav-link" active-class="active">短线</router-link>
          <router-link to="/extreme" class="nav-link" active-class="active">异动</router-link>
          <router-link to="/docs" class="nav-link" active-class="active">文档</router-link>
        </div>
        <div class="nav-status">
          <span class="dot" :class="wsConnected ? 'on' : 'off'"></span>
          <span class="n">{{ tickerCount }} 币种</span>
        </div>
      </div>
    </nav>
    <router-view />
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted } from 'vue'
import { coinApi } from '@/api'

export default {
  name: 'App',
  setup() {
    const wsConnected = ref(false)
    const tickerCount = ref(0)
    let t = null
    const check = async () => {
      try {
        const h = await coinApi.healthCheck()
        wsConnected.value = h.ws_connected
        tickerCount.value = h.ticker_count || 0
      } catch { wsConnected.value = false }
    }
    onMounted(() => { check(); t = setInterval(check, 8000) })
    onUnmounted(() => clearInterval(t))
    return { wsConnected, tickerCount }
  }
}
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700;800&display=swap');

* { margin:0; padding:0; box-sizing:border-box; }

body {
  font-family: 'Inter', -apple-system, sans-serif;
  background: #0d1117;
  color: #c9d1d9;
  -webkit-font-smoothing: antialiased;
  overflow: hidden;
}
#app {
  height: 100vh; display: flex; flex-direction: column;
  --el-text-color-regular: #c9d1d9;
  --el-text-color-primary: #f0f6fc;
  --el-text-color-secondary: #8b949e;
  --el-text-color-placeholder: #484f58;
  --el-bg-color: #161b22;
  --el-bg-color-overlay: #161b22;
  --el-border-color: #30363d;
  --el-border-color-light: #21262d;
  --el-fill-color-blank: #0d1117;
  --el-fill-color: #0d1117;
  --el-fill-color-light: #1c2128;
  --el-color-primary: #58a6ff;
  --el-color-primary-light-3: #3b82f6;
  --el-color-primary-light-5: #2563eb;
  --el-color-primary-light-7: #1d4ed8;
  --el-color-primary-light-9: #1e3a5f;
}

/* ---- Nav ---- */
.nav { background: #161b22; border-bottom: 1px solid #21262d; flex-shrink: 0; z-index: 100; }
.nav-inner { height: 48px; display: flex; align-items: center; padding: 0 20px; gap: 28px; }
.brand { display: flex; align-items: center; gap: 8px; text-decoration: none; }
.brand-mark { color: #58a6ff; font-size: 16px; }
.brand-text { color: #f0f6fc; font-weight: 700; font-size: 15px; letter-spacing: -0.3px; }
.nav-links { display:flex; gap:2px; }
.nav-link {
  padding: 6px 16px; border-radius: 6px; text-decoration: none;
  color: #8b949e; font-size: 13px; font-weight: 500; transition: all 0.12s;
}
.nav-link:hover { color: #c9d1d9; background: #1c2128; }
.nav-link.active { color: #f0f6fc; background: #1c2128; }

.nav-status { margin-left:auto; display:flex; align-items:center; gap:8px; }
.dot { width:7px; height:7px; border-radius:50%; }
.dot.on { background:#3fb950; box-shadow:0 0 6px #3fb95055; }
.dot.off { background:#f85149; }
.n { font-size:12px; color:#8b949e; font-weight:500; }

/* ---- Element Plus overrides ---- */

.el-table {
  --el-table-bg-color: transparent;
  --el-table-tr-bg-color: transparent;
  --el-table-header-bg-color: #0d1117;
  --el-table-row-hover-bg-color: #1a1f2b;
  --el-table-border-color: #1a1f2b;
  --el-table-text-color: #c9d1d9;
  --el-table-header-text-color: #8b949e;
  font-size: 13px;
  font-family: 'Inter', sans-serif;
}
.el-table th.el-table__cell {
  background: #0d1117;
  font-weight: 600;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.3px;
  padding: 10px 0;
  border-bottom: 1px solid #21262d;
}
.el-table td.el-table__cell {
  padding: 7px 0;
  border-bottom: 1px solid #161b22;
}
.el-table__body tr:hover > td.el-table__cell {
  background: #1a1f2b !important;
}
.el-table .cell { padding:0 14px; }
.el-table__empty-text { color:#484f58; }
.el-table__body tr { transition: background 0.1s; }
.el-table .sort-caret.ascending { border-bottom-color:#484f58; }
.el-table .sort-caret.descending { border-top-color:#484f58; }
.el-table .ascending .sort-caret.ascending { border-bottom-color:#58a6ff; }
.el-table .descending .sort-caret.descending { border-top-color:#58a6ff; }

.el-loading-mask { background:rgba(13,17,23,0.75); }
.el-loading-spinner .path { stroke:#58a6ff; }
.el-loading-spinner .el-loading-text { color:#8b949e; }

.el-dialog {
  background:#161b22; border:1px solid #21262d; border-radius:12px;
  box-shadow:0 12px 48px #00000055;
}
.el-dialog__header { padding:20px 24px 0; }
.el-dialog__title { color:#f0f6fc; font-weight:700; font-size:16px; }
.el-dialog__body { padding:16px 24px 24px; }

/* -- Drawer -- */
.el-drawer {
  background:#161b22 !important;
  border-left:1px solid #21262d;
}
.el-drawer__header {
  padding:18px 20px 0;
  margin-bottom:0;
}
.el-drawer__title {
  color:#f0f6fc; font-weight:700; font-size:15px;
}
.el-drawer__body {
  padding:16px 20px 24px;
}
.el-drawer__close-btn {
  color:#8b949e;
}
.el-drawer__close-btn:hover {
  color:#c9d1d9;
}

/* -- Input Number -- */
.el-input-number { width:auto; }
.el-input-number .el-input__wrapper {
  background:#0d1117; border:1px solid #30363d; border-radius:6px;
  box-shadow:none; transition:border-color 0.15s;
}
.el-input-number .el-input__wrapper:hover { border-color:#484f58; }
.el-input-number .el-input__wrapper.is-focus { border-color:#58a6ff; box-shadow:0 0 0 1px #58a6ff22; }
.el-input-number .el-input__inner {
  background:transparent; color:#f0f6fc; font-size:14px; font-family:'JetBrains Mono',monospace;
  text-align:left; height:30px; padding:0 8px;
}
.el-input-number.is-controls-right .el-input-number__decrease,
.el-input-number.is-controls-right .el-input-number__increase {
  background:#161b22; border-color:#30363d; color:#8b949e;
  width:24px; border-radius:0; transition:all 0.12s;
}
.el-input-number.is-controls-right .el-input-number__decrease:hover,
.el-input-number.is-controls-right .el-input-number__increase:hover {
  color:#c9d1d9; background:#21262d; border-color:#484f58;
}
.el-input-number.is-controls-right .el-input-number__decrease { border-radius:0 5px 0 0; }
.el-input-number.is-controls-right .el-input-number__increase { border-radius:0 0 5px 0; }

/* -- Select -- */
.el-select .el-input__wrapper {
  background:#0d1117; border:1px solid #30363d; border-radius:6px;
  box-shadow:none; transition:border-color 0.15s;
}
.el-select .el-input__wrapper:hover { border-color:#484f58; }
.el-select .el-input__wrapper.is-focus { border-color:#58a6ff; box-shadow:0 0 0 1px #58a6ff22; }
.el-select .el-input__inner {
  color:#f0f6fc; font-size:14px; font-family:'JetBrains Mono',monospace; height:30px;
}
.el-select .el-input .el-select__caret { color:#8b949e; }
.el-select .el-input .el-select__caret:hover { color:#c9d1d9; }
.el-select-dropdown {
  background:#161b22; border:1px solid #30363d; border-radius:6px; overflow:hidden;
  box-shadow:0 8px 24px #00000044;
}
.el-select-dropdown__item {
  color:#8b949e; font-size:13px; font-family:'JetBrains Mono',monospace;
  padding:8px 14px; transition:all 0.1s;
}
.el-select-dropdown__item.hover { background:#1c2128; color:#e6edf3; }
.el-select-dropdown__item.selected { color:#58a6ff; font-weight:600; background:#0d1117; }
.el-popper__arrow::before { background:#161b22; border:1px solid #30363d; }

::-webkit-scrollbar { width:5px; height:5px; }
::-webkit-scrollbar-track { background:#0d1117; }
::-webkit-scrollbar-thumb { background:#21262d; border-radius:3px; }
::-webkit-scrollbar-thumb:hover { background:#30363d; }
</style>
