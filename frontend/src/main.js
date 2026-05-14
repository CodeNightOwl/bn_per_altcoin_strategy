import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import App from './App.vue'
import CoinList from './components/CoinList.vue'
import ShortTermMovers from './components/ShortTermMovers.vue'
import ExtremeMovers from './components/ExtremeMovers.vue'
import DocsPage from './components/DocsPage.vue'

const routes = [
  { path: '/', redirect: '/coins' },
  { path: '/coins', component: CoinList },
  { path: '/short-term', component: ShortTermMovers },
  { path: '/extreme', component: ExtremeMovers },
  { path: '/docs', component: DocsPage }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

const app = createApp(App)

for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(ElementPlus)
app.use(router)
app.mount('#app')