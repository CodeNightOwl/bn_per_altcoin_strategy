<template>
  <div class="page">
    <div class="topbar">
      <div class="ctrls">
        <div class="ctrl">
          <label>周期</label>
          <el-select v-model="timeframe" @change="load" size="small" style="width:88px">
            <el-option v-for="t in ['5m','15m','30m','1h']" :key="t" :label="t" :value="t" />
          </el-select>
        </div>
        <div class="ctrl-sep"></div>
        <div class="ctrl">
          <label>阈值</label>
          <el-input-number v-model="threshold" :min="0.1" :max="20" :step="0.1" size="small" @change="load" style="width:120px" />
          <span class="unit">%</span>
        </div>
        <div class="ctrl-sep"></div>
        <div class="ctrl">
          <label>成交量≥</label>
          <el-input-number v-model="volMin" :min="0.1" :max="50" :step="0.5" size="small" @change="load" style="width:120px" />
          <span class="unit">M</span>
        </div>
      </div>
      <div class="actions">
        <span class="countdown" v-if="autoRefresh">{{ cd }}s</span>
        <button class="btn" @click="load" :disabled="loading">{{ loading?'刷新中':'刷新' }}</button>
      </div>
    </div>

    <div class="panels">
      <div class="panel">
        <div class="panel-hd gain">
          <div class="hd-left"><span class="hd-dot"></span> {{ timeframe }} 急涨 ≥ {{ threshold }}%</div>
          <span class="cnt">{{ data.gainers.length }}</span>
        </div>
        <div class="panel-body">
          <el-table :data="data.gainers" v-loading="loading" style="width:100%" height="100%" @row-click="showDetail" :default-sort="{prop:'short_term_change', order:'descending'}">
            <el-table-column prop="symbol" label="币种" width="130">
              <template #default="{ row }"><span class="sym">{{ row.symbol }}</span></template>
            </el-table-column>
            <el-table-column prop="price" label="价格" width="115" align="right">
              <template #default="{ row }"><span class="col-price">${{ fmtPrice(row.price) }}</span></template>
            </el-table-column>
            <el-table-column prop="short_term_change" :label="`${timeframe}涨跌`" width="90" sortable :sort-orders="['descending', 'ascending']" :sort-method="by('short_term_change')" align="right">
              <template #default="{ row }">
                <span class="up chg">{{ fmtPct(row.short_term_change) }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="change_24h" label="24H" width="85" sortable :sort-orders="['descending', 'ascending']" :sort-method="by('change_24h')" align="right">
              <template #default="{ row }">
                <span :class="clr(row.change_24h)+' chg'">{{ fmtPct(row.change_24h) }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="volume_24h" label="24H成交量" min-width="130" sortable align="right">
              <template #default="{ row }"><span class="col-vol">${{ fmtVol(row.volume_24h) }}</span></template>
            </el-table-column>
          </el-table>
        </div>
      </div>
      <div class="panel">
        <div class="panel-hd loss">
          <div class="hd-left"><span class="hd-dot"></span> {{ timeframe }} 急跌 ≤ -{{ threshold }}%</div>
          <span class="cnt">{{ data.losers.length }}</span>
        </div>
        <div class="panel-body">
          <el-table :data="data.losers" v-loading="loading" style="width:100%" height="100%" @row-click="showDetail" :default-sort="{prop:'short_term_change', order:'descending'}">
            <el-table-column prop="symbol" label="币种" width="130">
              <template #default="{ row }"><span class="sym">{{ row.symbol }}</span></template>
            </el-table-column>
            <el-table-column prop="price" label="价格" width="115" align="right">
              <template #default="{ row }"><span class="col-price">${{ fmtPrice(row.price) }}</span></template>
            </el-table-column>
            <el-table-column prop="short_term_change" :label="`${timeframe}涨跌`" width="90" sortable :sort-orders="['descending', 'ascending']" :sort-method="by('short_term_change')" align="right">
              <template #default="{ row }">
                <span class="down chg">{{ fmtPct(row.short_term_change) }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="change_24h" label="24H" width="85" sortable :sort-orders="['descending', 'ascending']" :sort-method="by('change_24h')" align="right">
              <template #default="{ row }">
                <span :class="clr(row.change_24h)+' chg'">{{ fmtPct(row.change_24h) }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="volume_24h" label="24H成交量" min-width="130" sortable align="right">
              <template #default="{ row }"><span class="col-vol">${{ fmtVol(row.volume_24h) }}</span></template>
            </el-table-column>
          </el-table>
        </div>
      </div>
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
          <div class="di">
            <span class="dil">{{ timeframe }}</span>
            <span :class="clr(selectedCoin?.short_term_change)" class="div">{{ fmtPct(selectedCoin?.short_term_change) }}</span>
          </div>
          <div class="di">
            <span class="dil">24H</span>
            <span :class="clr(selectedCoin?.change_24h)" class="div">{{ fmtPct(selectedCoin?.change_24h) }}</span>
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
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { coinApi } from '@/api'
import { createChart, CandlestickSeries } from 'lightweight-charts'

const data = ref({ gainers: [], losers: [] })
const loading = ref(false)
const threshold = ref(0.5)
const volMin = ref(0.5)
const timeframe = ref('5m')
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

const load = async () => {
  loading.value = true
  try {
    const res = await coinApi.getShortTermMovers({
      threshold: threshold.value, volume_threshold: volMin.value * 1e6, limit: 50, timeframe: timeframe.value
    })
    data.value = {
      ...res,
      gainers: [...(res.gainers || [])].sort((a, b) => (Math.abs(b.short_term_change) || 0) - (Math.abs(a.short_term_change) || 0)),
      losers: [...(res.losers || [])].sort((a, b) => (Math.abs(b.short_term_change) || 0) - (Math.abs(a.short_term_change) || 0))
    }
  } catch {} finally { loading.value = false }
}

const chartRef = ref(null)
let chart = null
let candleSeries = null

const initChart = async () => {
  await nextTick()
  if (!chartRef.value) { console.warn('ShortTermMovers: chartRef is null'); return }
  if (!selectedCoin.value) { console.warn('ShortTermMovers: selectedCoin is null'); return }
  try {
    const kd = await coinApi.getCoinKlines(selectedCoin.value.symbol, '1m', 50)
    console.log('ShortTermMovers klines:', kd)
    if (!kd.klines || kd.klines.length < 2) { console.warn('ShortTermMovers: no klines data'); return }

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
    console.log('ShortTermMovers: chart created with', kd.klines.length, 'candles')
  } catch (e) { console.error('ShortTermMovers chart:', e) }
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
  load()
  t2 = setInterval(() => { cd.value = cd.value > 1 ? cd.value - 1 : 8 }, 1000)
  t1 = setInterval(() => { if (autoRefresh.value) { cd.value = 8; load() } }, 8000)
})
onUnmounted(() => { clearInterval(t1); clearInterval(t2) })
</script>

<style scoped>
.page { flex:1; display:flex; flex-direction:column; padding:16px 20px; overflow:hidden; min-height:0; gap:12px; }

.topbar {
  display:flex; align-items:center; justify-content:space-between;
  padding:14px 24px; background:#161b22; border:1px solid #21262d; border-radius:10px; flex-shrink:0;
}
.ctrls { display:flex; gap:20px; align-items:center; }
.ctrl { display:flex; align-items:center; gap:8px; }
.ctrl label { font-size:12px; color:#8b949e; font-weight:500; }
.ctrl-sep { width:1px; height:20px; background:#21262d; }
.unit { font-size:12px; color:#484f58; }
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

.panels { flex:1; display:grid; grid-template-columns:1fr 1fr; gap:12px; min-height:0; }
.panel {
  background:#161b22; border:1px solid #21262d; border-radius:10px; display:flex; flex-direction:column; overflow:hidden;
}
.panel-hd {
  display:flex; justify-content:space-between; align-items:center;
  padding:12px 18px; font-size:13px; font-weight:600;
  border-bottom:1px solid #21262d; flex-shrink:0;
}
.panel-hd.gain { color:#3fb950; }
.panel-hd.loss { color:#f85149; }
.hd-left { display:flex; align-items:center; gap:8px; }
.hd-dot { width:8px; height:8px; border-radius:50%; background:currentColor; opacity:0.6; }
.cnt { font-family:'JetBrains Mono',monospace; font-size:18px; font-weight:800; }
.panel-body { flex:1; overflow:hidden; min-height:0; }

.sym { font-family:'JetBrains Mono',monospace; font-size:13px; font-weight:600; color:#f0f6fc; cursor:pointer; }
.sym:hover { color:#58a6ff; }
.col-price { font-family:'JetBrains Mono',monospace; font-size:13px; color:#b1bac4; }
.chg { font-family:'JetBrains Mono',monospace; font-size:13px; font-weight:600; }
.up.chg { color:#3fb950; }
.down.chg { color:#f85149; }
.col-vol { font-family:'JetBrains Mono',monospace; font-size:12px; color:#8b949e; }

.detail { text-align:center; padding:0 8px; }
.dp { font-family:'JetBrains Mono',monospace; font-size:28px; font-weight:800; color:#58a6ff; margin-bottom:20px; }
.dg { display:grid; grid-template-columns:repeat(3,1fr); gap:8px; }
.di { background:#0d1117; border-radius:8px; padding:14px 12px; display:flex; flex-direction:column; gap:4px; border:1px solid #21262d; }
.dil { font-size:10px; color:#484f58; text-transform:uppercase; font-weight:600; letter-spacing:0.5px; }
.div { font-family:'JetBrains Mono',monospace; font-size:15px; font-weight:700; }
.muted { color:#8b949e; }

.chart-wrap { height:260px; margin-top:16px; border-radius:8px; overflow:hidden; border:1px solid #21262d; }
</style>
