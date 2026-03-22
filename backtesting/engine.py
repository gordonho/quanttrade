"""
Backtesting Engine
基于历史数据回测策略，计算性能指标
"""

from decimal import Decimal
from typing import Dict, List, Optional, Any
from datetime import date, datetime, timedelta
from dataclasses import dataclass, field
import logging

from django.db import transaction
from django.utils import timezone

from market_data.models import Stock, DailyData
from strategies.models import Strategy, StrategySignal
from .models import Backtest, BacktestTrade, BacktestEquity

logger = logging.getLogger(__name__)


@dataclass
class Position:
    """持仓"""

    stock: Stock
    quantity: int = 0
    avg_cost: Decimal = Decimal("0")

    @property
    def market_value(self) -> Decimal:
        return Decimal("0")

    @property
    def profit_loss(self) -> Decimal:
        return Decimal("0")


@dataclass
class BacktestMetrics:
    """回测指标"""

    total_return: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    win_rate: float = 0.0
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    profit_factor: float = 0.0
    annual_return: float = 0.0
    volatility: float = 0.0


@dataclass
class DailySnapshot:
    """每日快照"""

    date: date
    cash: Decimal
    positions_value: Decimal
    total_value: Decimal
    daily_return: float


class BacktestEngine:
    """
    回测引擎

    运行策略回测，支持:
    - 多股票同时回测
    - 模拟撮合(市价单、滑点)
    - 手续费计算
    - 性能指标计算
    """

    def __init__(
        self,
        backtest_instance: Backtest,
        stock_codes: List[str] = None,
        progress_callback: Optional[callable] = None,
    ):
        self.backtest = backtest_instance
        self.strategy = backtest_instance.strategy
        self.user = backtest_instance.user

        self.start_date = backtest_instance.start_date
        self.end_date = backtest_instance.end_date
        self.initial_capital = Decimal(str(backtest_instance.initial_capital))
        self.commission_rate = Decimal(str(backtest_instance.commission))
        self.slippage_rate = Decimal(str(backtest_instance.slippage))

        self.stock_codes = stock_codes or []
        self.progress_callback = progress_callback

        self.current_date: Optional[date] = None
        self.current_price: Dict[str, Decimal] = {}

        self.cash = self.initial_capital
        self.positions: Dict[str, Position] = {}
        self.daily_snapshots: List[DailySnapshot] = []
        self.trades: List[Dict] = []

        self._equity_history: List[Decimal] = []
        self._running = False

    def get_stocks(self) -> List[Stock]:
        """获取回测股票"""
        if self.stock_codes:
            return Stock.objects.filter(code__in=self.stock_codes, is_active=True)
        return Stock.objects.filter(is_active=True)

    def get_historical_data(self, stock: Stock, end_dt: date) -> List[DailyData]:
        """获取历史数据"""
        return list(
            DailyData.objects.filter(
                stock=stock, date__gte=self.start_date, date__lte=end_dt
            ).order_by("date")
        )

    def generate_signals(self, current_date: date) -> List[Dict]:
        """生成交易信号"""
        signals = []
        stocks = self.get_stocks()

        strategy_class = self._get_strategy_class()
        if not strategy_class:
            return signals

        try:
            strategy = strategy_class(self.strategy, self.strategy.parameters)

            for stock in stocks:
                data = DailyData.objects.filter(
                    stock=stock, date__lte=current_date
                ).order_by("-date")[:60]

                if len(data) < 20:
                    continue

                signal = self._analyze_stock(strategy, stock, data, current_date)
                if signal:
                    signals.append(signal)

        except Exception as e:
            logger.error(f"信号生成失败: {e}")

        return signals

    def _get_strategy_class(self):
        """获取策略类"""
        from strategies.sample_strategy import get_strategy_class

        strategy_name = self.strategy.parameters.get("strategy_name", "ma_crossover")
        return get_strategy_class(strategy_name)

    def _analyze_stock(
        self, strategy, stock: Stock, data: list, current_date: date
    ) -> Optional[Dict]:
        """分析单只股票生成信号"""
        try:
            if len(data) < 2:
                return None

            closes = [float(d.close) for d in reversed(data)]
            short_window = self.strategy.parameters.get("short_window", 5)
            long_window = self.strategy.parameters.get("long_window", 20)

            if len(closes) < long_window + 1:
                return None

            ma_short = sum(closes[-short_window:]) / short_window
            ma_long = sum(closes[-long_window:]) / long_window

            ma_short_prev = sum(closes[-(short_window + 1) : -1]) / short_window
            ma_long_prev = sum(closes[-(long_window + 1) : -1]) / long_window

            current_price = closes[-1]

            if ma_short_prev <= ma_long_prev and ma_short > ma_long:
                return {
                    "stock": stock,
                    "signal_type": "buy",
                    "price": Decimal(str(current_price)),
                    "reason": f"金叉: MA{short_window}={ma_short:.2f} 上穿 MA{long_window}={ma_long:.2f}",
                }
            elif ma_short_prev >= ma_long_prev and ma_short < ma_long:
                return {
                    "stock": stock,
                    "signal_type": "sell",
                    "price": Decimal(str(current_price)),
                    "reason": f"死叉: MA{short_window}={ma_short:.2f} 下穿 MA{long_window}={ma_long:.2f}",
                }

        except Exception as e:
            logger.error(f"股票分析失败 {stock.code}: {e}")

        return None

    def execute_signal(self, signal: Dict) -> bool:
        """执行交易信号"""
        stock = signal["stock"]
        signal_type = signal["signal_type"]
        price = signal["price"]

        slippage_price = (
            price * (1 + self.slippage_rate)
            if signal_type == "buy"
            else price * (1 - self.slippage_rate)
        )
        exec_price = slippage_price.quantize(Decimal("0.01"))

        if signal_type == "buy":
            return self._execute_buy(stock, exec_price)
        else:
            return self._execute_sell(stock, exec_price)

    def _execute_buy(self, stock: Stock, price: Decimal) -> bool:
        """执行买入"""
        max_position_value = self.initial_capital * Decimal("0.2")
        available_cash = self.cash * Decimal("0.95")

        if available_cash < price * 100:
            return False

        position_value = min(max_position_value, available_cash)
        quantity = int(position_value / (price * 100)) * 100

        if quantity < 100:
            return False

        cost = price * quantity
        commission = cost * self.commission_rate
        total_cost = cost + commission

        if total_cost > self.cash:
            quantity = (
                int(
                    (self.cash * Decimal("0.95"))
                    / (price * (1 + self.commission_rate))
                    / 100
                )
                * 100
            )
            if quantity < 100:
                return False
            cost = price * quantity
            commission = cost * self.commission_rate
            total_cost = cost + commission

        self.cash -= total_cost

        if stock.code in self.positions:
            pos = self.positions[stock.code]
            total_quantity = pos.quantity + quantity
            pos.avg_cost = (
                pos.avg_cost * pos.quantity + price * quantity
            ) / total_quantity
            pos.quantity = total_quantity
        else:
            self.positions[stock.code] = Position(
                stock=stock, quantity=quantity, avg_cost=price
            )

        self.trades.append(
            {
                "stock": stock,
                "signal_type": "buy",
                "price": price,
                "quantity": quantity,
                "commission": commission,
                "datetime": timezone.make_aware(
                    datetime.combine(self.current_date, datetime.min.time())
                ),
            }
        )

        return True

    def _execute_sell(self, stock: Stock, price: Decimal) -> bool:
        """执行卖出"""
        if stock.code not in self.positions:
            return False

        pos = self.positions[stock.code]
        quantity = pos.quantity

        revenue = price * quantity
        commission = revenue * self.commission_rate
        net_revenue = revenue - commission

        self.cash += net_revenue
        pos.quantity = 0
        del self.positions[stock.code]

        self.trades.append(
            {
                "stock": stock,
                "signal_type": "sell",
                "price": price,
                "quantity": quantity,
                "commission": commission,
                "datetime": timezone.make_aware(
                    datetime.combine(self.current_date, datetime.min.time())
                ),
            }
        )

        return True

    def update_positions_value(self, prices: Dict[str, Decimal]) -> Decimal:
        """更新持仓市值"""
        total = Decimal("0")
        for code, pos in self.positions.items():
            if code in prices:
                pos.avg_cost = pos.avg_cost
            total += pos.market_value
        return total

    def calculate_daily_return(
        self, prev_value: Decimal, current_value: Decimal
    ) -> float:
        """计算日收益率"""
        if prev_value == 0:
            return 0.0
        return float((current_value - prev_value) / prev_value)

    def calculate_metrics(self) -> BacktestMetrics:
        """计算回测指标"""
        metrics = BacktestMetrics()

        if not self.daily_snapshots or len(self.daily_snapshots) < 2:
            return metrics

        final_value = self.daily_snapshots[-1].total_value
        initial_value = self.daily_snapshots[0].total_value

        metrics.total_return = (
            float((final_value - initial_value) / initial_value) * 100
        )

        returns = [s.daily_return for s in self.daily_snapshots[1:]]
        if returns:
            avg_return = sum(returns) / len(returns)
            variance = sum((r - avg_return) ** 2 for r in returns) / len(returns)
            volatility = variance**0.5

            metrics.volatility = volatility * 100

            if volatility > 0:
                annual_return = avg_return * 252
                metrics.sharpe_ratio = annual_return / (volatility * (252**0.5))

            metrics.annual_return = avg_return * 252 * 100

        peak = initial_value
        max_drawdown = 0
        for snapshot in self.daily_snapshots:
            if snapshot.total_value > peak:
                peak = snapshot.total_value
            drawdown = (peak - snapshot.total_value) / peak
            if drawdown > max_drawdown:
                max_drawdown = drawdown

        metrics.max_drawdown = max_drawdown * 100

        winning = 0
        losing = 0
        win_amount = 0
        loss_amount = 0

        for trade in self.trades:
            if trade["signal_type"] == "sell":
                prev_pos = next(
                    (
                        t
                        for t in reversed(self.trades)
                        if t["stock"] == trade["stock"]
                        and t["signal_type"] == "buy"
                        and t["datetime"] < trade["datetime"]
                    ),
                    None,
                )
                if prev_pos:
                    profit = (
                        (trade["price"] - prev_pos["price"]) * trade["quantity"]
                        - trade["commission"]
                        - prev_pos["commission"]
                    )
                    if profit > 0:
                        winning += 1
                        win_amount += profit
                    else:
                        losing += 1
                        loss_amount += abs(profit)

        metrics.total_trades = winning + losing
        metrics.winning_trades = winning
        metrics.losing_trades = losing

        if metrics.total_trades > 0:
            metrics.win_rate = (winning / metrics.total_trades) * 100

        if winning > 0:
            metrics.avg_win = float(win_amount / winning)
        if losing > 0:
            metrics.avg_loss = float(loss_amount / losing)

        if metrics.avg_loss > 0:
            metrics.profit_factor = metrics.avg_win / metrics.avg_loss

        return metrics

    def run(self) -> BacktestMetrics:
        """运行回测"""
        self._running = True
        logger.info(
            f"开始回测: {self.strategy.name} ({self.start_date} ~ {self.end_date})"
        )

        try:
            self.backtest.status = "running"
            self.backtest.save()

            stocks = list(self.get_stocks())
            if not stocks:
                raise ValueError("没有可回测的股票")

            stock_codes = [s.code for s in stocks]

            all_dates = set()
            for stock in stocks:
                dates = DailyData.objects.filter(
                    stock=stock, date__gte=self.start_date, date__lte=self.end_date
                ).values_list("date", flat=True)
                all_dates.update(dates)

            trading_dates = sorted(all_dates)

            if not trading_dates:
                raise ValueError("没有历史数据")

            logger.info(
                f"回测期间: {len(trading_dates)} 个交易日, {len(stocks)} 只股票"
            )

            for i, current_date in enumerate(trading_dates):
                self.current_date = current_date

                prices = {}
                for stock in stocks:
                    data = DailyData.objects.filter(
                        stock=stock, date=current_date
                    ).first()
                    if data:
                        prices[stock.code] = data.close

                signals = self.generate_signals(current_date)
                for signal in signals:
                    self.execute_signal(signal)

                positions_value = Decimal("0")
                for code, pos in self.positions.items():
                    if code in prices:
                        positions_value += prices[code] * pos.quantity

                total_value = self.cash + positions_value

                prev_value = (
                    self.daily_snapshots[-1].total_value
                    if self.daily_snapshots
                    else self.initial_capital
                )
                daily_return = self.calculate_daily_return(prev_value, total_value)

                self.daily_snapshots.append(
                    DailySnapshot(
                        date=current_date,
                        cash=self.cash,
                        positions_value=positions_value,
                        total_value=total_value,
                        daily_return=daily_return,
                    )
                )

                if self.progress_callback and (i + 1) % 10 == 0:
                    self.progress_callback(i + 1, len(trading_dates))

            metrics = self.calculate_metrics()
            self._save_results(metrics)

            self.backtest.status = "completed"
            self.backtest.final_capital = self.daily_snapshots[-1].total_value
            self.backtest.total_return = metrics.total_return
            self.backtest.sharpe_ratio = metrics.sharpe_ratio
            self.backtest.max_drawdown = metrics.max_drawdown
            self.backtest.win_rate = metrics.win_rate
            self.backtest.total_trades = metrics.total_trades
            self.backtest.completed_at = timezone.now()
            self.backtest.save()

            logger.info(
                f"回测完成: 总收益={metrics.total_return:.2f}%, 夏普={metrics.sharpe_ratio:.2f}"
            )

            return metrics

        except Exception as e:
            logger.error(f"回测失败: {e}")
            self.backtest.status = "failed"
            self.backtest.error_message = str(e)
            self.backtest.save()
            raise

        finally:
            self._running = False

    @transaction.atomic
    def _save_results(self, metrics: BacktestMetrics):
        """保存回测结果"""
        BacktestTrade.objects.filter(backtest=self.backtest).delete()
        BacktestEquity.objects.filter(backtest=self.backtest).delete()

        for trade in self.trades:
            BacktestTrade.objects.create(
                backtest=self.backtest,
                stock=trade["stock"],
                signal_type=trade["signal_type"],
                price=trade["price"],
                quantity=trade["quantity"],
                commission=trade["commission"],
                datetime=trade["datetime"],
            )

        for snapshot in self.daily_snapshots:
            BacktestEquity.objects.create(
                backtest=self.backtest,
                date=snapshot.date,
                total_value=snapshot.total_value,
                cash=snapshot.cash,
                positions_value=snapshot.positions_value,
                daily_return=snapshot.daily_return,
            )

    def get_equity_curve(self) -> List[Dict]:
        """获取权益曲线"""
        return [
            {
                "date": s.date.isoformat(),
                "total_value": float(s.total_value),
                "cash": float(s.cash),
                "positions_value": float(s.positions_value),
                "daily_return": s.daily_return,
            }
            for s in self.daily_snapshots
        ]

    def get_trade_history(self) -> List[Dict]:
        """获取交易历史"""
        return [
            {
                "datetime": t["datetime"].isoformat(),
                "stock_code": t["stock"].code,
                "stock_name": t["stock"].name,
                "signal_type": t["signal_type"],
                "price": float(t["price"]),
                "quantity": t["quantity"],
                "amount": float(t["price"] * t["quantity"]),
                "commission": float(t["commission"]),
            }
            for t in self.trades
        ]


def run_backtest(
    backtest_id: int,
    stock_codes: List[str] = None,
    progress_callback: Optional[callable] = None,
) -> BacktestMetrics:
    """
    运行回测的便捷函数
    """
    backtest = Backtest.objects.select_related("strategy", "user").get(id=backtest_id)
    engine = BacktestEngine(backtest, stock_codes, progress_callback)
    return engine.run()
