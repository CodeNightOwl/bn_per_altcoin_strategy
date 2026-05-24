<template>
  <div class="page">
    <div class="topbar">
      <div class="stats">
        <div class="stat-card">
          <span class="sc-num">{{ coins.length }}</span>
          <span class="sc-label">列表币种</span>
        </div>
        <div class="stat-card">
          <span class="sc-num" :class="stats.avg_change_24h>=0?'up':'down'">{{ fmtPct(stats.avg_change_24h) }}</span>
          <span class="sc-label">24H 均幅</span>
        </div>
        <div class="stat-card gain">
          <span class="sc-num up">▲ {{ upCount }}</span>
          <span class="sc-label">上涨</span>
        </div>
        <div class="stat-card loss">
          <span class="sc-num down">▼ {{ downCount }}</span>
          <span class="sc-label">下跌</span>
        </div>
      </div>
      <div class="actions">
        <span class="countdown" v-if="autoRefresh">{{ cd }}s</span>
        <button class="btn" @click="loadData" :disabled="loading">{{ loading?'刷新中':'刷新' }}</button>
      </div>
    </div>

    <div class="table-wrap">
      <el-table
        :data="coins" v-loading="loading" style="width:100%" height="100%"
        @row-click="showDetail"
        :default-sort="{prop:'max_change', order:'descending'}"
      >
        <el-table-column prop="symbol" label="币种" width="140" fixed>
          <template #default="{ row }">
            <span class="sym">{{ row.symbol }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="price" label="最新价" width="120" align="right">
          <template #default="{ row }">
            <span class="price">${{ fmtPrice(row.price) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="change_1m" label="1分" width="80" align="right" sortable :sort-orders="['descending', 'ascending']" :sort-method="by('change_1m')">
          <template #default="{ row }">
            <span v-if="row.change_1m!=null" :class="clr(row.change_1m)+' chg'">{{ fmtPct(row.change_1m) }}</span>
            <span v-else class="na">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="change_5m" label="5分" width="80" align="right" sortable :sort-orders="['descending', 'ascending']" :sort-method="by('change_5m')">
          <template #default="{ row }">
            <span v-if="row.change_5m!=null" :class="clr(row.change_5m)+' chg'">{{ fmtPct(row.change_5m) }}</span>
            <span v-else class="na">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="change_15m" label="15分" width="80" align="right" sortable :sort-orders="['descending', 'ascending']" :sort-method="by('change_15m')">
          <template #default="{ row }">
            <span v-if="row.change_15m!=null" :class="clr(row.change_15m)+' chg'">{{ fmtPct(row.change_15m) }}</span>
            <span v-else class="na">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="change_30m" label="30分" width="80" align="right" sortable :sort-orders="['descending', 'ascending']" :sort-method="by('change_30m')">
          <template #default="{ row }">
            <span v-if="row.change_30m!=null" :class="clr(row.change_30m)+' chg'">{{ fmtPct(row.change_30m) }}</span>
            <span v-else class="na">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="change_1h" label="1时" width="80" align="right" sortable :sort-orders="['descending', 'ascending']" :sort-method="by('change_1h')">
          <template #default="{ row }">
            <span v-if="row.change_1h!=null" :class="clr(row.change_1h)+' chg'">{{ fmtPct(row.change_1h) }}</span>
            <span v-else class="na">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="max_change" label="波幅" width="84" align="right" sortable :sort-orders="['descending', 'ascending']" :sort-method="by('max_change')">
          <template #default="{ row }">
            <span :class="clr(row.max_change)+' chg bold'">{{ fmtPct(row.max_change) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="change_24h" label="24H" width="80" align="right" sortable :sort-orders="['descending', 'ascending']" :sort-method="by('change_24h')">
          <template #default="{ row }">
            <span :class="clr(row.change_24h)+' chg'">{{ fmtPct(row.change_24h) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="volume_24h" label="24H成交量" min-width="130" align="right" sortable>
          <template #default="{ row }">
            <span class="vol">${{ fmtVol(row.volume_24h) }}</span>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-drawer
      v-model="dlg.visible"
      :title="selectedCoin?.symbol"
      direction="rtl"
      size="480px"
      class="coin-drawer"
      destroy-on-close
      @close="onClose"
    >
      <div class="detail">
        <div class="dp">${{ fmtPrice(selectedCoin?.price) }}</div>
        <div class="dg">
          <div class="di" v-for="tf in ['1m','5m','15m','30m','1h','24h']" :key="tf">
            <span class="dil">{{ tf }}</span>
            <span :class="clr(selectedCoin?.[`change_${tf}`])" class="div">{{ fmtPct(selectedCoin?.[`change_${tf}`]) }}</span>
          </div>
          <div class="di">
            <span class="dil">成交</span>
            <span class="div muted">${{ fmtVol(selectedCoin?.volume_24h) }}</span>
          </div>
        </div>
        <div class="chart-wrap" ref="chartRef"></div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { coinApi } from '@/api'
import { createChart, CandlestickSeries } from 'lightweight-charts'

const coins = ref([])
const stats = ref({ total_altcoins: 0, avg_change_24h: 0, gainers_count: 0, losers_count: 0 })
const loading = ref(false)
const autoRefresh = ref(true)
const cd = ref(8)
const dlg = ref({ visible: false })
const selectedCoin = ref(null)
let t1 = null, t2 = null

const fmtPrice = p => p != null ? (p >= 1 ? p.toFixed(p < 10 ? 4 : 2) : p.toFixed(6)) : '-'
const fmtPct = v => v != null ? `${v >= 0 ? '+' : ''}${v.toFixed(2)}%` : '-'
const fmtVol = v => { if (!v) return '0'; if (v >= 1e9) return (v / 1e9).toFixed(2) + 'B'; if (v >= 1e6) return (v / 1e6).toFixed(2) + 'M'; return (v / 1e3).toFixed(1) + 'K' }
const clr = v => v > 0 ? 'up' : v < 0 ? 'down' : ''
const by = p => (a, b) => (Math.abs(a?.[p]) || 0) - (Math.abs(b?.[p]) || 0)
const upCount = computed(() => coins.value.filter(c => (c.change_24h || 0) > 0).length)
const downCount = computed(() => coins.value.filter(c => (c.change_24h || 0) < 0).length)

const loadData = async () => {
  loading.value = true
  try {
    const [s, data] = await Promise.all([
      coinApi.getStats(),
      coinApi.getTimeframeChanges({ limit: 80, timeframes: '1m,5m,15m,30m,1h', volume_threshold: 5000000 })
    ])
    stats.value = s
    if (data.coins) {
      coins.value = [...data.coins].sort((a, b) =>
        (Math.abs(b.max_change) || 0) - (Math.abs(a.max_change) || 0)
      )
    }
  } catch {} finally { loading.value = false }
}

const chartRef = ref(null)
let chart = null
let candleSeries = null

const initChart = async () => {
  await nextTick()
  if (!chartRef.value) { console.warn('CoinList: chartRef is null'); return }
  if (!selectedCoin.value) { console.warn('CoinList: selectedCoin is null'); return }
  try {
    const kd = await coinApi.getCoinKlines(selectedCoin.value.symbol, '5m', 100)
    console.log('CoinList klines:', kd)
    if (!kd.klines || kd.klines.length < 2) { console.warn('CoinList: no klines data'); return }

    await new Promise(r => setTimeout(r, 350))

    chart = createChart(chartRef.value, {
      width: chartRef.value.clientWidth,
      height: 260,
      layout: {
        background: { color: '#0d1117' },
        textColor: '#8b949e'
      },
      grid: {
        vertLines: { color: '#161b22' },
        horzLines: { color: '#161b22' }
      },
      crosshair: { mode: 0 },
      localization: {
        timeFormatter: (time) => {
          if (typeof time === 'number') {
            const d = new Date(time * 1000)
            return d.toLocaleString('zh-CN', {
              timeZone: 'Asia/Shanghai',
              year: 'numeric', month: '2-digit', day: '2-digit',
              hour: '2-digit', minute: '2-digit', second: '2-digit',
              hour12: false
            })
          }
          return String(time)
        }
      },
      rightPriceScale: { borderColor: '#21262d' },
      timeScale: {
        borderColor: '#21262d',
        timeVisible: true,
        secondsVisible: false,
        tickMarkFormatter: (time) => {
          const d = new Date(time * 1000)
          return d.toLocaleString('zh-CN', {
            timeZone: 'Asia/Shanghai',
            month: '2-digit', day: '2-digit',
            hour: '2-digit', minute: '2-digit',
            hour12: false
          })
        }
      }
    })

    candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: '#3fb950',
      downColor: '#f85149',
      borderDownColor: '#f85149',
      borderUpColor: '#3fb950',
      wickDownColor: '#f85149',
      wickUpColor: '#3fb950'
    })
    candleSeries.setData(kd.klines)
    chart.timeScale().fitContent()
    console.log('CoinList: chart created with', kd.klines.length, 'candles')
  } catch (e) { console.error('CoinList chart:', e) }
}

const showDetail = coin => {
  selectedCoin.value = coin
  autoRefresh.value = false
  dlg.value.visible = true
}

const onClose = () => {
  if (chart) { chart.remove(); chart = null; candleSeries = null }
  selectedCoin.value = null
  dlg.value.visible = false
  autoRefresh.value = true
}

watch(() => dlg.value.visible, async (visible) => {
  if (visible) {
    await nextTick()
    initChart()
  }
})

onMounted(() => {
  loadData()
  t2 = setInterval(() => { cd.value = cd.value > 1 ? cd.value - 1 : 8 }, 1000)
  t1 = setInterval(() => { if (autoRefresh.value) { cd.value = 8; loadData() } }, 8000)
})
onUnmounted(() => { clearInterval(t1); clearInterval(t2) })
</script>

<style scoped>
.page { flex:1; display:flex; flex-direction:column; padding:16px 20px; overflow:hidden; min-height:0; gap:12px; }

.topbar {
  display:flex; align-items:center; justify-content:space-between;
  padding:16px 24px; background:#161b22; border:1px solid #21262d; border-radius:10px; flex-shrink:0;
}
.stats { display:flex; gap:40px; }
.stat-card { display:flex; flex-direction:column; gap:4px; }
.sc-num { font-family:'JetBrains Mono',monospace; font-size:22px; font-weight:800; color:#e6edf3; letter-spacing:-0.5px; }
.sc-num.up { color:#3fb950; }
.sc-num.down { color:#f85149; }
.sc-label { font-size:11px; color:#484f58; font-weight:500; text-transform:uppercase; letter-spacing:0.5px; }
.actions { display:flex; align-items:center; gap:14px; }

.countdown {
  font-family:'JetBrains Mono',monospace; font-size:13px; color:#484f58;
  background:#0d1117; padding:4px 10px; border-radius:4px; min-width:36px; text-align:center;
}

.btn {
  padding:8px 24px; background:#21262d; color:#c9d1d9; border:1px solid #30363d; border-radius:6px;
  font-weight:600; font-size:13px; cursor:pointer; transition:all 0.15s; font-family:inherit;
}
.btn:hover { background:#30363d; border-color:#58a6ff; color:#f0f6fc; }
.btn:disabled { opacity:0.4; cursor:not-allowed; }

.table-wrap { flex:1; background:#161b22; border:1px solid #21262d; border-radius:10px; overflow:hidden; min-height:0; }

.sym { font-family:'JetBrains Mono',monospace; font-size:13px; font-weight:600; color:#f0f6fc; cursor:pointer; }
.sym:hover { color:#58a6ff; }
.price { font-family:'JetBrains Mono',monospace; font-size:13px; color:#c9d1d9; }
.chg { font-family:'JetBrains Mono',monospace; font-size:13px; font-weight:600; }
.up.chg { color:#3fb950; }
.down.chg { color:#f85149; }
.bold { font-weight:700; }
.na { color:#484f58; font-family:'JetBrains Mono',monospace; font-size:13px; }
.vol { font-family:'JetBrains Mono',monospace; font-size:12px; color:#8b949e; }

.detail { text-align:center; padding:0 8px; }
.dp { font-family:'JetBrains Mono',monospace; font-size:28px; font-weight:800; color:#58a6ff; margin-bottom:20px; }
.dg { display:grid; grid-template-columns:repeat(3,1fr); gap:8px; }
.di { background:#0d1117; border-radius:8px; padding:14px 12px; display:flex; flex-direction:column; gap:4px; border:1px solid #21262d; }
.dil { font-size:10px; color:#484f58; text-transform:uppercase; font-weight:600; letter-spacing:0.5px; }
.div { font-family:'JetBrains Mono',monospace; font-size:15px; font-weight:700; }
.muted { color:#8b949e; }

.chart-wrap { height:260px; margin-top:16px; border-radius:8px; overflow:hidden; border:1px solid #21262d; }
</style>
