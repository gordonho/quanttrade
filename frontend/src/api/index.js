// API 配置
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

// 获取 token
function getToken() {
  return localStorage.getItem('token')
}

// 设置 token
function setToken(token) {
  localStorage.setItem('token', token)
}

// 移除 token
function removeToken() {
  localStorage.removeItem('token')
}

// 通用请求方法
async function request(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`
  const token = getToken()
  
  const headers = {
    'Content-Type': 'application/json',
    ...(token && { 'Authorization': `Bearer ${token}` }),
    ...options.headers
  }

  try {
    const response = await fetch(url, {
      ...options,
      headers
    })

    if (response.status === 401) {
      removeToken()
      window.location.href = '/login'
      throw new Error('未授权，请重新登录')
    }

    const data = await response.json()
    
    if (!response.ok) {
      throw new Error(data.message || '请求失败')
    }
    
    return data
  } catch (error) {
    console.error('API Error:', error)
    throw error
  }
}

// 用户 API
export const authAPI = {
  login: async (username, password) => {
    const response = await fetch(`${API_BASE_URL}/token/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    })
    if (!response.ok) {
      throw new Error('登录失败')
    }
    const data = await response.json()
    return { access: data.access, ...data.user }
  },
  
  register: async (userData) => {
    const response = await fetch(`${API_BASE_URL}/users/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(userData)
    })
    if (!response.ok) {
      throw new Error('注册失败')
    }
    return response.json()
  },
  
  getProfile: () => 
    request('/users/me/'),
}

// 股票 API
export const stockAPI = {
  list: (params) => {
    const query = new URLSearchParams(params).toString()
    return request(`/market/stocks/?${query}`)
  },
  
  get: (code) => 
    request(`/market/stocks/${code}/`),
  
  getDailyData: (code, params) => {
    const query = new URLSearchParams(params).toString()
    return request(`/market/daily/?stock=${code}&${query}`)
  },
}

// 策略 API
export const strategyAPI = {
  list: () => request('/strategies/'),
  
  get: (id) => request(`/strategies/${id}/`),
  
  create: (data) => request('/strategies/', { method: 'POST', body: JSON.stringify(data) }),
  
  update: (id, data) => request(`/strategies/${id}/`, { method: 'PUT', body: JSON.stringify(data) }),
  
  delete: (id) => request(`/strategies/${id}/`, { method: 'DELETE' }),
  
  start: (id) => request(`/strategies/${id}/start/`, { method: 'POST' }),
  
  stop: (id) => request(`/strategies/${id}/stop/`, { method: 'POST' }),
}

// 回测 API
export const backtestAPI = {
  list: () => request('/backtesting/backtests/'),
  
  create: (data) => request('/backtesting/backtests/', { method: 'POST', body: JSON.stringify(data) }),
  
  get: (id) => request(`/backtesting/backtests/${id}/`),
  
  getResults: (id) => request(`/backtesting/backtests/${id}/results/`),
  
  getTrades: (id) => request(`/backtesting/backtests/${id}/trades/`),
}

// 交易 API
export const tradingAPI = {
  getOrders: (params) => {
    const query = new URLSearchParams(params).toString()
    return request(`/trading/orders/?${query}`)
  },
  
  createOrder: (data) => request('/trading/orders/', { method: 'POST', body: JSON.stringify(data) }),
  
  cancelOrder: (id) => request(`/trading/orders/${id}/cancel/`, { method: 'POST' }),
  
  getPositions: () => request('/trading/positions/'),
  
  getTrades: () => request('/trading/trades/'),
}

// 组合 API
export const portfolioAPI = {
  list: () => request('/portfolio/portfolios/'),
  
  get: (id) => request(`/portfolio/portfolios/${id}/`),
  
  create: (data) => request('/portfolio/portfolios/', { method: 'POST', body: JSON.stringify(data) }),
  
  getHistory: (id) => request(`/portfolio/portfolios/${id}/history/`),
}

export default {
  auth: authAPI,
  stock: stockAPI,
  strategy: strategyAPI,
  backtest: backtestAPI,
  trading: tradingAPI,
  portfolio: portfolioAPI,
  getToken,
  setToken,
  removeToken
}
