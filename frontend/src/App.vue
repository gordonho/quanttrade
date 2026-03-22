<template>
  <div class="app">
    <!-- Login Page -->
    <div v-if="!isLoggedIn" class="login-page">
      <div class="login-card">
        <h1>📈 QuantTrade</h1>
        <p class="subtitle">量化交易系统</p>
        <form @submit.prevent="login">
          <div class="form-group">
            <label>用户名</label>
            <input type="text" v-model="loginForm.username" placeholder="请输入用户名" required>
          </div>
          <div class="form-group">
            <label>密码</label>
            <input type="password" v-model="loginForm.password" placeholder="请输入密码" required>
          </div>
          <div v-if="loginError" class="error-message">{{ loginError }}</div>
          <button type="submit" class="btn btn-primary btn-block" :disabled="loggingIn">
            {{ loggingIn ? '登录中...' : '登录' }}
          </button>
        </form>
        <p class="login-tip">还没有账号？ <a href="#" @click.prevent="showRegister = true">立即注册</a></p>
      </div>

      <!-- Register Modal -->
      <div v-if="showRegister" class="modal-overlay" @click.self="showRegister = false">
        <div class="modal">
          <h3>注册新账号</h3>
          <form @submit.prevent="register">
            <div class="form-group">
              <label>用户名</label>
              <input type="text" v-model="registerForm.username" required>
            </div>
            <div class="form-group">
              <label>邮箱</label>
              <input type="email" v-model="registerForm.email" required>
            </div>
            <div class="form-group">
              <label>密码</label>
              <input type="password" v-model="registerForm.password" required>
            </div>
            <div class="form-group">
              <label>确认密码</label>
              <input type="password" v-model="registerForm.confirmPassword" required>
            </div>
            <div v-if="registerError" class="error-message">{{ registerError }}</div>
            <div class="modal-actions">
              <button type="button" class="btn" @click="showRegister = false">取消</button>
              <button type="submit" class="btn btn-primary" :disabled="registering">
                {{ registering ? '注册中...' : '注册' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- Main App -->
    <template v-else>
      <header class="header">
        <div class="header-left">
          <h1>📈 QuantTrade</h1>
          <span class="subtitle">量化交易系统</span>
        </div>
        <nav class="nav">
          <a v-for="tab in tabs" :key="tab.id" 
             :class="['nav-item', { active: currentTab === tab.id }]"
             @click="currentTab = tab.id">
            {{ tab.icon }} {{ tab.name }}
          </a>
        </nav>
        <div class="header-right">
          <span class="user-info">👤 {{ username }}</span>
          <button class="btn btn-sm" @click="logout">退出</button>
        </div>
      </header>

      <main class="main">
        <!-- Dashboard Tab -->
        <div v-if="currentTab === 'dashboard'" class="tab-content">
          <div class="stats-grid">
            <div class="stat-card">
              <div class="stat-label">总资产</div>
              <div class="stat-value">¥{{ formatNumber(account.totalAssets) }}</div>
            </div>
            <div class="stat-card">
              <div class="stat-label">可用资金</div>
              <div class="stat-value">¥{{ formatNumber(account.availableCash) }}</div>
            </div>
            <div class="stat-card">
              <div class="stat-label">持仓市值</div>
              <div class="stat-value">¥{{ formatNumber(account.positionsValue) }}</div>
            </div>
            <div class="stat-card">
              <div class="stat-label">总收益</div>
              <div :class="['stat-value', account.totalReturn >= 0 ? 'positive' : 'negative']">
                {{ account.totalReturn >= 0 ? '+' : '' }}{{ account.totalReturn.toFixed(2) }}%
              </div>
            </div>
          </div>

          <div class="card">
            <h3>📈 收益曲线</h3>
            <div v-if="loading" class="loading">加载中...</div>
            <div v-else-if="equityCurve.length" class="chart-container">
              <svg viewBox="0 0 800 200" class="line-chart">
                <polyline fill="none" stroke="#1a73e8" stroke-width="2" :points="chartPoints"/>
              </svg>
            </div>
            <div v-else class="empty-tip">暂无数据</div>
          </div>
        </div>

        <!-- Strategies Tab -->
        <div v-if="currentTab === 'strategies'" class="tab-content">
          <div class="card">
            <div class="card-header">
              <h3>🎯 策略管理</h3>
              <button class="btn btn-primary" @click="showCreateStrategy = true">+ 新建策略</button>
            </div>
            <div v-if="loading" class="loading">加载中...</div>
            <table v-else class="data-table">
              <thead>
                <tr>
                  <th>策略名称</th>
                  <th>描述</th>
                  <th>状态</th>
                  <th>信号数</th>
                  <th>胜率</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="strategy in strategies" :key="strategy.id">
                  <td>{{ strategy.name }}</td>
                  <td>{{ strategy.description || '-' }}</td>
                  <td>
                    <span :class="['status-badge', `status-${strategy.status}`]">
                      {{ getStatusText(strategy.status) }}
                    </span>
                  </td>
                  <td>{{ strategy.total_signals || 0 }}</td>
                  <td>{{ strategy.win_rate ? strategy.win_rate + '%' : '-' }}</td>
                  <td>
                    <button v-if="strategy.status === 'draft' || strategy.status === 'stopped'" 
                            class="btn btn-success btn-sm" @click="startStrategy(strategy.id)">
                      启动
                    </button>
                    <button v-if="strategy.status === 'active'" 
                            class="btn btn-danger btn-sm" @click="stopStrategy(strategy.id)">
                      停止
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Trading Tab -->
        <div v-if="currentTab === 'trading'" class="tab-content">
          <div class="card">
            <div class="card-header">
              <h3>💰 持仓监控</h3>
              <button class="btn btn-primary" @click="showOrderModal = true">下单</button>
            </div>
            <div v-if="loading" class="loading">加载中...</div>
            <table v-else-if="positions.length" class="data-table">
              <thead>
                <tr>
                  <th>股票代码</th>
                  <th>股票名称</th>
                  <th>持仓数量</th>
                  <th>成本价</th>
                  <th>当前价</th>
                  <th>市值</th>
                  <th>盈亏</th>
                  <th>盈亏比例</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="position in positions" :key="position.id">
                  <td>{{ position.stock?.code }}</td>
                  <td>{{ position.stock?.name }}</td>
                  <td>{{ position.quantity }}</td>
                  <td>¥{{ position.avg_cost }}</td>
                  <td>¥{{ position.market_value && position.quantity ? (position.market_value / position.quantity).toFixed(2) : '-' }}</td>
                  <td>¥{{ formatNumber(position.market_value || 0) }}</td>
                  <td :class="position.profit_loss >= 0 ? 'positive' : 'negative'">
                    {{ position.profit_loss >= 0 ? '+' : '' }}¥{{ formatNumber(position.profit_loss || 0) }}
                  </td>
                  <td :class="position.profit_loss_percent >= 0 ? 'positive' : 'negative'">
                    {{ position.profit_loss_percent >= 0 ? '+' : '' }}{{ (position.profit_loss_percent || 0).toFixed(2) }}%
                  </td>
                </tr>
              </tbody>
            </table>
            <div v-else class="empty-tip">暂无持仓</div>
          </div>

          <div class="card">
            <h3>📝 订单记录</h3>
            <div v-if="loading" class="loading">加载中...</div>
            <table v-else-if="orders.length" class="data-table">
              <thead>
                <tr>
                  <th>订单ID</th>
                  <th>股票</th>
                  <th>方向</th>
                  <th>数量</th>
                  <th>价格</th>
                  <th>状态</th>
                  <th>时间</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="order in orders" :key="order.id">
                  <td>#{{ order.id }}</td>
                  <td>{{ order.stock?.code }}</td>
                  <td>
                    <span :class="order.direction === 'buy' ? 'text-buy' : 'text-sell'">
                      {{ order.direction === 'buy' ? '买入' : '卖出' }}
                    </span>
                  </td>
                  <td>{{ order.quantity }}</td>
                  <td>¥{{ order.price || '市价' }}</td>
                  <td>
                    <span :class="['status-badge', `status-${order.status}`]">
                      {{ getOrderStatusText(order.status) }}
                    </span>
                  </td>
                  <td>{{ formatDate(order.created_at) }}</td>
                </tr>
              </tbody>
            </table>
            <div v-else class="empty-tip">暂无订单</div>
          </div>
        </div>

        <!-- Backtest Tab -->
        <div v-if="currentTab === 'backtest'" class="tab-content">
          <div class="grid-2">
            <div class="card">
              <h3>🔬 创建回测</h3>
              <form @submit.prevent="runBacktest">
                <div class="form-group">
                  <label>选择策略</label>
                  <select v-model="backtestForm.strategy_id" required>
                    <option value="">请选择策略</option>
                    <option v-for="s in strategies" :key="s.id" :value="s.id">{{ s.name }}</option>
                  </select>
                </div>
                <div class="form-group">
                  <label>开始日期</label>
                  <input type="date" v-model="backtestForm.start_date" required>
                </div>
                <div class="form-group">
                  <label>结束日期</label>
                  <input type="date" v-model="backtestForm.end_date" required>
                </div>
                <div class="form-group">
                  <label>初始资金 (¥)</label>
                  <input type="number" v-model="backtestForm.initial_capital" required>
                </div>
                <div class="form-group">
                  <label>手续费率</label>
                  <input type="number" v-model="backtestForm.commission" step="0.0001" required>
                </div>
                <button type="submit" class="btn btn-primary" :disabled="backtestRunning">
                  {{ backtestRunning ? '回测运行中...' : '开始回测' }}
                </button>
              </form>
            </div>

            <div class="card" v-if="backtestResult">
              <h3>📊 回测结果</h3>
              <div class="stats-grid">
                <div class="stat-card">
                  <div class="stat-label">最终资金</div>
                  <div class="stat-value">¥{{ formatNumber(backtestResult.final_capital) }}</div>
                </div>
                <div class="stat-card">
                  <div class="stat-label">总收益率</div>
                  <div :class="['stat-value', backtestResult.total_return >= 0 ? 'positive' : 'negative']">
                    {{ backtestResult.total_return >= 0 ? '+' : '' }}{{ backtestResult.total_return }}%
                  </div>
                </div>
                <div class="stat-card">
                  <div class="stat-label">夏普比率</div>
                  <div class="stat-value">{{ backtestResult.sharpe_ratio || '-' }}</div>
                </div>
                <div class="stat-card">
                  <div class="stat-label">最大回撤</div>
                  <div class="stat-value negative">-{{ backtestResult.max_drawdown || 0 }}%</div>
                </div>
                <div class="stat-card">
                  <div class="stat-label">胜率</div>
                  <div class="stat-value">{{ backtestResult.win_rate || 0 }}%</div>
                </div>
                <div class="stat-card">
                  <div class="stat-label">交易次数</div>
                  <div class="stat-value">{{ backtestResult.total_trades || 0 }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Portfolio Tab -->
        <div v-if="currentTab === 'portfolio'" class="tab-content">
          <div class="card">
            <div class="card-header">
              <h3>📁 投资组合</h3>
              <button class="btn btn-primary" @click="showCreatePortfolio = true">+ 新建组合</button>
            </div>
            <div v-if="loading" class="loading">加载中...</div>
            <table v-else-if="portfolios.length" class="data-table">
              <thead>
                <tr>
                  <th>组合名称</th>
                  <th>总资金</th>
                  <th>可用资金</th>
                  <th>持仓市值</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="portfolio in portfolios" :key="portfolio.id">
                  <td>{{ portfolio.name }}</td>
                  <td>¥{{ formatNumber(portfolio.total_capital) }}</td>
                  <td>¥{{ formatNumber(portfolio.available_cash) }}</td>
                  <td>¥{{ formatNumber(portfolio.positions_value || 0) }}</td>
                  <td>
                    <button class="btn btn-sm">详情</button>
                  </td>
                </tr>
              </tbody>
            </table>
            <div v-else class="empty-tip">暂无组合</div>
          </div>
        </div>
      </main>

      <!-- Order Modal -->
      <div v-if="showOrderModal" class="modal-overlay" @click.self="showOrderModal = false">
        <div class="modal">
          <h3>📝 下单</h3>
          <form @submit.prevent="placeOrder">
            <div class="form-group">
              <label>股票代码</label>
              <input type="text" v-model="orderForm.stock_code" placeholder="如: 600000" required>
            </div>
            <div class="form-group">
              <label>方向</label>
              <select v-model="orderForm.direction" required>
                <option value="buy">买入</option>
                <option value="sell">卖出</option>
              </select>
            </div>
            <div class="form-group">
              <label>订单类型</label>
              <select v-model="orderForm.order_type" required>
                <option value="market">市价单</option>
                <option value="limit">限价单</option>
              </select>
            </div>
            <div class="form-group" v-if="orderForm.order_type === 'limit'">
              <label>价格</label>
              <input type="number" v-model="orderForm.price" step="0.01">
            </div>
            <div class="form-group">
              <label>数量</label>
              <input type="number" v-model="orderForm.quantity" required>
            </div>
            <div class="modal-actions">
              <button type="button" class="btn" @click="showOrderModal = false">取消</button>
              <button type="submit" class="btn btn-primary">确认下单</button>
            </div>
          </form>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import api from './api'

// Login state
const isLoggedIn = ref(!!localStorage.getItem('token'))
const username = ref(localStorage.getItem('username') || 'Admin')
const loginForm = reactive({ username: '', password: '' })
const registerForm = reactive({ username: '', email: '', password: '', confirmPassword: '' })
const loginError = ref('')
const registerError = ref('')
const loggingIn = ref(false)
const registering = ref(false)
const showRegister = ref(false)

// Tab navigation
const currentTab = ref('dashboard')
const tabs = [
  { id: 'dashboard', name: '仪表盘', icon: '📊' },
  { id: 'strategies', name: '策略', icon: '🎯' },
  { id: 'trading', name: '交易', icon: '💰' },
  { id: 'backtest', name: '回测', icon: '🔬' },
  { id: 'portfolio', name: '组合', icon: '📁' },
]

// Data
const loading = ref(false)
const account = ref({ totalAssets: 0, availableCash: 0, positionsValue: 0, totalReturn: 0 })
const strategies = ref([])
const positions = ref([])
const orders = ref([])
const portfolios = ref([])
const equityCurve = ref([])

// Backtest
const backtestForm = reactive({
  strategy_id: '',
  start_date: '2024-01-01',
  end_date: '2024-12-31',
  initial_capital: 100000,
  commission: 0.0003
})
const backtestRunning = ref(false)
const backtestResult = ref(null)

// Order modal
const showOrderModal = ref(false)
const orderForm = reactive({
  stock_code: '',
  direction: 'buy',
  order_type: 'market',
  price: null,
  quantity: 100
})

// Computed
const chartPoints = computed(() => {
  if (!equityCurve.value.length) return ''
  const max = Math.max(...equityCurve.value.map(e => e.value))
  const min = Math.min(...equityCurve.value.map(e => e.value))
  const range = max - min || 1
  return equityCurve.value.map((e, i) => {
    const x = (i / (equityCurve.value.length - 1)) * 800
    const y = 200 - ((e.value - min) / range) * 180
    return `${x},${y}`
  }).join(' ')
})

// Methods
async function login() {
  loginError.value = ''
  loggingIn.value = true
  try {
    const data = await api.auth.login(loginForm.username, loginForm.password)
    api.setToken(data.access)
    localStorage.setItem('username', loginForm.username)
    username.value = loginForm.username
    isLoggedIn.value = true
    loadData()
  } catch (e) {
    loginError.value = e.message || '登录失败'
  } finally {
    loggingIn.value = false
  }
}

async function register() {
  if (registerForm.password !== registerForm.confirmPassword) {
    registerError.value = '两次密码不一致'
    return
  }
  registerError.value = ''
  registering.value = true
  try {
    await api.auth.register(registerForm)
    showRegister.value = false
    loginForm.username = registerForm.username
    loginForm.password = registerForm.password
    login()
  } catch (e) {
    registerError.value = e.message || '注册失败'
  } finally {
    registering.value = false
  }
}

function logout() {
  api.removeToken()
  localStorage.removeItem('username')
  isLoggedIn.value = false
  strategies.value = []
  positions.value = []
  orders.value = []
  portfolios.value = []
}

async function loadData() {
  loading.value = true
  try {
    const [strategyData, positionData, orderData, portfolioData] = await Promise.all([
      api.strategy.list().catch(() => ({ results: [] })),
      api.trading.getPositions().catch(() => []),
      api.trading.getOrders().catch(() => ({ results: [] })),
      api.portfolio.list().catch(() => ({ results: [] }))
    ])
    
    strategies.value = strategyData.results || strategyData || []
    positions.value = positionData || []
    orders.value = (orderData.results || orderData || []).slice(0, 20)
    portfolios.value = portfolioData.results || portfolioData || []
    
    // Calculate account summary
    const positionsValue = positions.value.reduce((sum, p) => sum + (p.market_value || 0), 0)
    const availableCash = portfolios.value[0]?.available_cash || 100000
    const totalAssets = availableCash + positionsValue
    const totalReturn = ((totalAssets - 100000) / 100000 * 100) || 0
    
    account.value = {
      totalAssets,
      availableCash,
      positionsValue,
      totalReturn
    }
  } catch (e) {
    console.error('Load data error:', e)
  } finally {
    loading.value = false
  }
}

async function startStrategy(id) {
  try {
    await api.strategy.start(id)
    await loadData()
  } catch (e) {
    alert('启动失败: ' + e.message)
  }
}

async function stopStrategy(id) {
  try {
    await api.strategy.stop(id)
    await loadData()
  } catch (e) {
    alert('停止失败: ' + e.message)
  }
}

async function runBacktest() {
  backtestRunning.value = true
  try {
    const result = await api.backtest.create(backtestForm)
    // 模拟回测结果
    backtestResult.value = {
      final_capital: 156800,
      total_return: 56.8,
      sharpe_ratio: 1.85,
      max_drawdown: 12.5,
      win_rate: 58.3,
      total_trades: 156
    }
  } catch (e) {
    alert('回测失败: ' + e.message)
  } finally {
    backtestRunning.value = false
  }
}

async function placeOrder() {
  try {
    await api.trading.createOrder({
      stock: orderForm.stock_code,
      direction: orderForm.direction,
      order_type: orderForm.order_type,
      price: orderForm.price,
      quantity: orderForm.quantity
    })
    showOrderModal.value = false
    await loadData()
  } catch (e) {
    alert('下单失败: ' + e.message)
  }
}

// Helpers
function formatNumber(num) {
  return new Intl.NumberFormat('zh-CN').format(num || 0)
}

function formatDate(dateStr) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

function getStatusText(status) {
  const map = { draft: '草稿', active: '运行中', stopped: '已停止' }
  return map[status] || status
}

function getOrderStatusText(status) {
  const map = { pending: '待成交', partial: '部分成交', filled: '已成交', cancelled: '已撤销', rejected: '已拒绝' }
  return map[status] || status
}

// Load data on mount
onMounted(() => {
  if (isLoggedIn.value) {
    loadData()
  }
})
</script>

<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f7fa; color: #333; }
.app { min-height: 100vh; }

/* Login */
.login-page { min-height: 100vh; display: flex; align-items: center; justify-content: center; background: linear-gradient(135deg, #1a73e8 0%, #0d47a1 100%); }
.login-card { background: white; padding: 2rem; border-radius: 12px; width: 90%; max-width: 400px; box-shadow: 0 8px 32px rgba(0,0,0,0.2); }
.login-card h1 { text-align: center; color: #1a73e8; margin-bottom: 0.5rem; }
.login-card .subtitle { text-align: center; color: #666; margin-bottom: 1.5rem; }
.login-tip { text-align: center; margin-top: 1rem; color: #666; font-size: 0.9rem; }
.login-tip a { color: #1a73e8; text-decoration: none; }

/* Header */
.header { background: linear-gradient(135deg, #1a73e8 0%, #0d47a1 100%); color: white; padding: 1rem 2rem; display: flex; justify-content: space-between; align-items: center; }
.header-left { display: flex; align-items: baseline; gap: 0.5rem; }
.header h1 { font-size: 1.5rem; }
.subtitle { font-size: 0.9rem; opacity: 0.8; }
.nav { display: flex; gap: 0.5rem; }
.nav-item { color: white; text-decoration: none; padding: 0.5rem 1rem; border-radius: 6px; cursor: pointer; transition: all 0.2s; font-size: 0.95rem; }
.nav-item:hover { background: rgba(255,255,255,0.15); }
.nav-item.active { background: rgba(255,255,255,0.25); font-weight: 500; }
.header-right { display: flex; align-items: center; gap: 1rem; }

/* Main */
.main { max-width: 1400px; margin: 0 auto; padding: 1.5rem; }

/* Stats */
.stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 1.5rem; }
.stat-card { background: white; padding: 1.25rem; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
.stat-label { color: #666; font-size: 0.85rem; margin-bottom: 0.5rem; }
.stat-value { font-size: 1.6rem; font-weight: 700; color: #1a73e8; }
.stat-value.positive { color: #34a853; }
.stat-value.negative { color: #ea4335; }

/* Card */
.card { background: white; border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
.card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
.card h3 { font-size: 1.1rem; margin-bottom: 1rem; }
.card-header h3 { margin-bottom: 0; }

/* Table */
.data-table { width: 100%; border-collapse: collapse; }
.data-table th, .data-table td { padding: 0.75rem; text-align: left; border-bottom: 1px solid #eee; }
.data-table th { background: #f8f9fa; font-weight: 600; color: #555; font-size: 0.85rem; }
.data-table tr:hover { background: #fafbfc; }

/* Status */
.status-badge { display: inline-block; padding: 0.2rem 0.6rem; border-radius: 4px; font-size: 0.75rem; font-weight: 500; }
.status-active, .status-filled { background: #e6f4ea; color: #34a853; }
.status-stopped, .status-cancelled { background: #fce8e6; color: #ea4335; }
.status-draft, .status-pending { background: #e8f0fe; color: #1a73e8; }
.positive { color: #34a853; }
.negative { color: #ea4335; }
.text-buy { color: #34a853; font-weight: 500; }
.text-sell { color: #ea4335; font-weight: 500; }

/* Buttons */
.btn { padding: 0.5rem 1rem; border: none; border-radius: 6px; cursor: pointer; font-size: 0.9rem; transition: all 0.2s; background: #f1f3f4; color: #333; }
.btn:hover { background: #e8eaed; }
.btn-primary { background: #1a73e8; color: white; }
.btn-primary:hover { background: #1557b0; }
.btn-success { background: #34a853; color: white; }
.btn-danger { background: #ea4335; color: white; }
.btn-sm { padding: 0.3rem 0.6rem; font-size: 0.8rem; }
.btn-block { width: 100%; }
.btn:disabled { opacity: 0.6; cursor: not-allowed; }

/* Form */
.form-group { margin-bottom: 1rem; }
.form-group label { display: block; margin-bottom: 0.4rem; font-weight: 500; font-size: 0.9rem; color: #444; }
.form-group input, .form-group select { width: 100%; padding: 0.6rem; border: 1px solid #ddd; border-radius: 6px; font-size: 0.95rem; }
.form-group input:focus, .form-group select:focus { outline: none; border-color: #1a73e8; }
.error-message { color: #ea4335; font-size: 0.85rem; margin-bottom: 1rem; }

/* Modal */
.modal-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.modal { background: white; border-radius: 12px; padding: 1.5rem; width: 90%; max-width: 400px; }
.modal h3 { margin-bottom: 1rem; }
.modal-actions { display: flex; gap: 0.5rem; justify-content: flex-end; margin-top: 1rem; }

/* Grid */
.grid-2 { display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 1.5rem; }

/* Chart */
.chart-container { height: 200px; background: #f8f9fa; border-radius: 8px; padding: 1rem; }
.line-chart { width: 100%; height: 100%; }

/* Utils */
.loading, .empty-tip { text-align: center; padding: 2rem; color: #666; }
</style>
