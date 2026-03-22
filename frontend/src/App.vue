<template>
  <div class="app">
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

        <div class="charts-section">
          <div class="card">
            <h3>收益曲线</h3>
            <div class="chart-placeholder">
              <div class="mock-chart">
                <svg viewBox="0 0 800 200" class="line-chart">
                  <polyline fill="none" stroke="#1a73e8" stroke-width="2" 
                    points="0,150 100,140 200,145 300,120 400,130 500,100 600,90 700,80 800,70"/>
                </svg>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Strategies Tab -->
      <div v-if="currentTab === 'strategies'" class="tab-content">
        <div class="card">
          <div class="card-header">
            <h3>🎯 策略管理</h3>
            <button class="btn btn-primary" @click="showCreateStrategy = true">+ 新建策略</button>
          </div>
          <table class="data-table">
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
                <td>{{ strategy.description }}</td>
                <td>
                  <span :class="['status-badge', `status-${strategy.status}`]">
                    {{ getStatusText(strategy.status) }}
                  </span>
                </td>
                <td>{{ strategy.total_signals }}</td>
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
          <table class="data-table">
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
                <td>{{ position.stock_code }}</td>
                <td>{{ position.stock_name }}</td>
                <td>{{ position.quantity }}</td>
                <td>¥{{ position.avg_cost }}</td>
                <td>¥{{ position.current_price }}</td>
                <td>¥{{ formatNumber(position.market_value) }}</td>
                <td :class="position.profit_loss >= 0 ? 'positive' : 'negative'">
                  {{ position.profit_loss >= 0 ? '+' : '' }}¥{{ formatNumber(position.profit_loss) }}
                </td>
                <td :class="position.profit_loss_percent >= 0 ? 'positive' : 'negative'">
                  {{ position.profit_loss_percent >= 0 ? '+' : '' }}{{ position.profit_loss_percent.toFixed(2) }}%
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="card">
          <h3>📝 订单记录</h3>
          <table class="data-table">
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
                <td>{{ order.stock_code }}</td>
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
                <div class="stat-value">{{ backtestResult.sharpe_ratio }}</div>
              </div>
              <div class="stat-card">
                <div class="stat-label">最大回撤</div>
                <div class="stat-value negative">-{{ backtestResult.max_drawdown }}%</div>
              </div>
              <div class="stat-card">
                <div class="stat-label">胜率</div>
                <div class="stat-value">{{ backtestResult.win_rate }}%</div>
              </div>
              <div class="stat-card">
                <div class="stat-label">交易次数</div>
                <div class="stat-value">{{ backtestResult.total_trades }}</div>
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
          <table class="data-table">
            <thead>
              <tr>
                <th>组合名称</th>
                <th>总资金</th>
                <th>可用资金</th>
                <th>持仓市值</th>
                <th>日收益</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="portfolio in portfolios" :key="portfolio.id">
                <td>{{ portfolio.name }}</td>
                <td>¥{{ formatNumber(portfolio.total_capital) }}</td>
                <td>¥{{ formatNumber(portfolio.available_cash) }}</td>
                <td>¥{{ formatNumber(portfolio.positions_value) }}</td>
                <td :class="portfolio.daily_return >= 0 ? 'positive' : 'negative'">
                  {{ portfolio.daily_return >= 0 ? '+' : '' }}{{ portfolio.daily_return }}%
                </td>
                <td>
                  <button class="btn btn-sm">详情</button>
                </td>
              </tr>
            </tbody>
          </table>
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
            <input type="text" v-model="orderForm.stock_code" placeholder="如: 000001" required>
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
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'

// Tab navigation
const currentTab = ref('dashboard')
const tabs = [
  { id: 'dashboard', name: '仪表盘', icon: '📊' },
  { id: 'strategies', name: '策略', icon: '🎯' },
  { id: 'trading', name: '交易', icon: '💰' },
  { id: 'backtest', name: '回测', icon: '🔬' },
  { id: 'portfolio', name: '组合', icon: '📁' },
]

const username = 'Admin'

// Account data
const account = ref({
  totalAssets: 156800,
  availableCash: 80000,
  positionsValue: 76800,
  totalReturn: 5.2
})

// Strategies
const strategies = ref([
  { id: 1, name: 'MA5 MA20 金叉策略', description: '移动平均线交叉策略', status: 'active', total_signals: 156, win_rate: 62.5 },
  { id: 2, name: 'RSI 超买超卖策略', description: 'RSI指标策略', status: 'stopped', total_signals: 89, win_rate: 55.3 },
  { id: 3, name: 'MACD 策略', description: 'MACD金叉死叉', status: 'draft', total_signals: 0, win_rate: null },
])

// Positions
const positions = ref([
  { id: 1, stock_code: '000001', stock_name: '平安银行', quantity: 1000, avg_cost: 12.50, current_price: 13.20, market_value: 13200, profit_loss: 700, profit_loss_percent: 5.6 },
  { id: 2, stock_code: '600519', stock_name: '贵州茅台', quantity: 100, avg_cost: 1800, current_price: 1850, market_value: 185000, profit_loss: 5000, profit_loss_percent: 2.78 },
])

// Orders
const orders = ref([
  { id: 1001, stock_code: '000001', direction: 'buy', quantity: 1000, price: 12.50, status: 'filled', created_at: '2024-01-15 10:30:00' },
  { id: 1002, stock_code: '600519', direction: 'buy', quantity: 100, price: 1800, status: 'filled', created_at: '2024-01-16 14:20:00' },
])

// Portfolios
const portfolios = ref([
  { id: 1, name: '主组合', total_capital: 100000, available_cash: 80000, positions_value: 20000, daily_return: 0.8 },
])

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

// Helpers
function formatNumber(num) {
  return new Intl.NumberFormat('zh-CN').format(num)
}

function formatDate(dateStr) {
  return dateStr
}

function getStatusText(status) {
  const map = { draft: '草稿', active: '运行中', stopped: '已停止' }
  return map[status] || status
}

function getOrderStatusText(status) {
  const map = { pending: '待成交', partial: '部分成交', filled: '已成交', cancelled: '已撤销' }
  return map[status] || status
}

function startStrategy(id) {
  console.log('Start strategy:', id)
}

function stopStrategy(id) {
  console.log('Stop strategy:', id)
}

function runBacktest() {
  backtestRunning.value = true
  setTimeout(() => {
    backtestResult.value = {
      final_capital: 156800,
      total_return: 56.8,
      sharpe_ratio: 1.85,
      max_drawdown: 12.5,
      win_rate: 58.3,
      total_trades: 156
    }
    backtestRunning.value = false
  }, 2000)
}

function placeOrder() {
  console.log('Place order:', orderForm)
  showOrderModal.value = false
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: #f5f7fa;
  color: #333;
}

.app {
  min-height: 100vh;
}

.header {
  background: linear-gradient(135deg, #1a73e8 0%, #0d47a1 100%);
  color: white;
  padding: 1rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2px 8px rgba(0,0,0,0.15);
}

.header-left {
  display: flex;
  align-items: baseline;
  gap: 0.5rem;
}

.header h1 {
  font-size: 1.5rem;
}

.subtitle {
  font-size: 0.9rem;
  opacity: 0.8;
}

.nav {
  display: flex;
  gap: 0.5rem;
}

.nav-item {
  color: white;
  text-decoration: none;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 0.95rem;
}

.nav-item:hover {
  background: rgba(255,255,255,0.15);
}

.nav-item.active {
  background: rgba(255,255,255,0.25);
  font-weight: 500;
}

.header-right {
  font-size: 0.9rem;
}

.main {
  max-width: 1400px;
  margin: 0 auto;
  padding: 1.5rem;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.stat-card {
  background: white;
  padding: 1.25rem;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}

.stat-label {
  color: #666;
  font-size: 0.85rem;
  margin-bottom: 0.5rem;
}

.stat-value {
  font-size: 1.6rem;
  font-weight: 700;
  color: #1a73e8;
}

.stat-value.positive {
  color: #34a853;
}

.stat-value.negative {
  color: #ea4335;
}

.card {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.card h3 {
  font-size: 1.1rem;
  margin-bottom: 1rem;
}

.card-header h3 {
  margin-bottom: 0;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th,
.data-table td {
  padding: 0.75rem;
  text-align: left;
  border-bottom: 1px solid #eee;
}

.data-table th {
  background: #f8f9fa;
  font-weight: 600;
  color: #555;
  font-size: 0.85rem;
}

.data-table tr:hover {
  background: #fafbfc;
}

.status-badge {
  display: inline-block;
  padding: 0.2rem 0.6rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 500;
}

.status-active, .status-filled {
  background: #e6f4ea;
  color: #34a853;
}

.status-stopped, .status-cancelled {
  background: #fce8e6;
  color: #ea4335;
}

.status-draft, .status-pending {
  background: #e8f0fe;
  color: #1a73e8;
}

.positive {
  color: #34a853;
}

.negative {
  color: #ea4335;
}

.text-buy {
  color: #34a853;
  font-weight: 500;
}

.text-sell {
  color: #ea4335;
  font-weight: 500;
}

.btn {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.2s;
  background: #f1f3f4;
  color: #333;
}

.btn:hover {
  background: #e8eaed;
}

.btn-primary {
  background: #1a73e8;
  color: white;
}

.btn-primary:hover {
  background: #1557b0;
}

.btn-success {
  background: #34a853;
  color: white;
}

.btn-success:hover {
  background: #2d8e47;
}

.btn-danger {
  background: #ea4335;
  color: white;
}

.btn-danger:hover {
  background: #c62828;
}

.btn-sm {
  padding: 0.3rem 0.6rem;
  font-size: 0.8rem;
}

.grid-2 {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 1.5rem;
}

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.4rem;
  font-weight: 500;
  font-size: 0.9rem;
  color: #444;
}

.form-group input,
.form-group select {
  width: 100%;
  padding: 0.6rem;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 0.95rem;
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: #1a73e8;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  width: 90%;
  max-width: 400px;
}

.modal h3 {
  margin-bottom: 1rem;
}

.modal-actions {
  display: flex;
  gap: 0.5rem;
  justify-content: flex-end;
  margin-top: 1rem;
}

.chart-placeholder {
  height: 200px;
  background: #f8f9fa;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.mock-chart {
  width: 100%;
  height: 100%;
}

.line-chart {
  width: 100%;
  height: 100%;
}
</style>
