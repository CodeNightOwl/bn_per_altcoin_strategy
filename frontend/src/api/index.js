import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 60000
})

api.interceptors.response.use(
  response => response.data,
  error => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

export const coinApi = {
  updateCoins: () => api.post('/coins/update'),
  
  getCoins: (params = {}) => api.get('/coins', { params }),
  
  getGainers: (limit = 20) => api.get('/coins/gainers', { params: { limit } }),
  
  getLosers: (limit = 20) => api.get('/coins/losers', { params: { limit } }),
  
  getExtremeMovers: (threshold = 10) => api.get('/coins/extreme', { params: { threshold } }),
  
  getShortTermMovers: (params = {}) => api.get('/coins/short-term-movers', { params }),
  
  getTimeframeChanges: (params = {}) => api.get('/coins/timeframe-changes', { params }),
  
  getCoinDetail: (symbol) => api.get(`/coins/${symbol}`),

  getCoinKlines: (symbol, timeframe = '5m', limit = 100) =>
    api.get('/coins/klines', { params: { symbol, timeframe, limit } }),

  getStats: () => api.get('/stats'),
  
  getConfig: () => api.get('/config'),
  
  healthCheck: () => api.get('/health'),
  
  connectWebSocket: () => api.post('/ws/connect'),
  
  disconnectWebSocket: () => api.post('/ws/disconnect'),
  
  subscribeSymbols: (symbols, timeframes = ['5m', '15m', '30m']) => 
    api.post('/ws/subscribe', { symbols, timeframes }),
  
  getWebSocketStatus: () => api.get('/ws/status'),
  
  getWebSocketData: () => api.get('/ws/data')
}

export default api