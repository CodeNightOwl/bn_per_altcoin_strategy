<template>
  <div class="docs">
    <aside class="sidebar">
      <div class="sidebar-title">策略文档</div>
      <button
        v-for="doc in docs" :key="doc.key"
        :class="['side-item', { active: active === doc.key }]"
        @click="active = doc.key"
      >
        <span class="si-num">{{ doc.icon }}</span>
        <span>{{ doc.label }}</span>
      </button>
    </aside>
    <main class="content">
      <div class="markdown-body" v-html="html"></div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import MarkdownIt from 'markdown-it'
const md = new MarkdownIt({ breaks:true, linkify:true })

const docs = [
  { key:'选标策略', label:'选标策略', icon:'01', file:'/选标策略.md' },
  { key:'开单策略', label:'开单策略', icon:'02', file:'/开单策略.md' },
  { key:'仓位管理', label:'仓位管理', icon:'03', file:'/仓位管理.md' },
  { key:'风险控制', label:'风险控制', icon:'04', file:'/风险控制.md' }
]
const active = ref('选标策略')
const contents = ref({})
const html = computed(() => md.render(contents.value[active.value]||''))

onMounted(async () => {
  for (const doc of docs) {
    try { const r=await fetch(doc.file); contents.value[doc.key]=await r.text() }
    catch { contents.value[doc.key]='# 加载失败' }
  }
})
</script>

<style scoped>
.docs { flex:1; display:flex; min-height:0; overflow:hidden; }

.sidebar {
  width:190px; flex-shrink:0; background:#161b22; border-right:1px solid #21262d; padding:20px 0; overflow-y:auto;
}
.sidebar-title {
  padding:0 16px 14px; font-size:11px; font-weight:600;
  color:#484f58; letter-spacing:1px; text-transform:uppercase;
}
.side-item {
  display:flex; align-items:center; gap:8px; width:100%; padding:9px 16px;
  border:none; background:transparent; color:#8b949e; font-size:13px; font-weight:500;
  cursor:pointer; transition:all 0.1s; text-align:left; font-family:inherit;
}
.side-item:hover { color:#c9d1d9; background:#1c2128; }
.side-item.active { color:#f0f6fc; background:#1c2128; box-shadow:inset 2px 0 0 #58a6ff; }
.si-num { font-size:10px; font-weight:700; opacity:0.3; width:16px; font-family:'JetBrains Mono',monospace; }

.content { flex:1; padding:28px 40px; overflow-y:auto; max-height:calc(100vh - 44px); }

.markdown-body { color:#b1bac4; line-height:1.75; font-size:14px; max-width:700px; }
.markdown-body :deep(h1) { font-size:24px; font-weight:700; color:#f0f6fc; margin:0 0 24px; padding-bottom:12px; border-bottom:1px solid #21262d; }
.markdown-body :deep(h2) { font-size:17px; font-weight:600; color:#e6edf3; margin:32px 0 12px; }
.markdown-body :deep(h3) { font-size:14px; font-weight:600; color:#c9d1d9; margin:20px 0 8px; }
.markdown-body :deep(p) { margin:0 0 12px; color:#8b949e; }
.markdown-body :deep(ul), .markdown-body :deep(ol) { margin:0 0 12px; padding-left:20px; color:#8b949e; }
.markdown-body :deep(li) { margin-bottom:4px; }
.markdown-body :deep(strong) { color:#e6edf3; font-weight:600; }
.markdown-body :deep(code) { background:#21262d; padding:2px 6px; border-radius:4px; font-size:12px; color:#d2a8ff; font-family:'JetBrains Mono',monospace; }
.markdown-body :deep(pre) { background:#0d1117; padding:14px; border-radius:8px; overflow-x:auto; margin:12px 0; border:1px solid #21262d; }
.markdown-body :deep(pre code) { background:none; padding:0; color:#c9d1d9; }
.markdown-body :deep(table) { width:100%; border-collapse:collapse; margin:14px 0; font-size:13px; }
.markdown-body :deep(th) { background:#0d1117; padding:8px 14px; text-align:left; font-weight:600; color:#8b949e; border-bottom:1px solid #21262d; font-size:12px; }
.markdown-body :deep(td) { padding:7px 14px; border-bottom:1px solid #161b22; color:#b1bac4; }
.markdown-body :deep(tr:hover td) { background:#1c2128; }
.markdown-body :deep(blockquote) { margin:12px 0; padding:10px 16px; background:#0d1117; border-left:2px solid #58a6ff; border-radius:0 6px 6px 0; color:#8b949e; font-size:13px; }
.markdown-body :deep(hr) { border:none; height:1px; background:#21262d; margin:24px 0; }
</style>
