"""
Sample Strategy: Moving Average Crossover
简单均线交叉策略
"""

from decimal import Decimal
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from django.db.models import Avg, Max, Min
from strategies.models import Strategy, StrategySignal, StrategyParameter
from market_data.models import Stock, DailyData


class MovingAverageCrossoverStrategy:
    """
    移动平均线交叉策略

    策略逻辑:
    - 短期均线上穿长期均线 -> 买入信号
    - 短期均线下穿长期均线 -> 卖出信号
    """

    name = "均线交叉策略"
    version = "1.0.0"
    description = "使用短期和长期移动平均线的交叉来生成交易信号"

    default_parameters = {
        "short_window": 5,  # 短期均线周期
        "long_window": 20,  # 长期均线周期
        "stock_codes": [],  # 关注的股票代码列表
        "max_positions": 5,  # 最大持仓数量
        "position_size": 0.2,  # 每只股票仓位比例
    }

    def __init__(self, strategy_instance: Strategy, parameters: Optional[Dict] = None):
        self.strategy_instance = strategy_instance
        self.parameters = {**self.default_parameters, **(parameters or {})}
        self.short_window = self.parameters["short_window"]
        self.long_window = self.parameters["long_window"]
        self.max_positions = self.parameters["max_positions"]
        self.position_size = self.parameters["position_size"]

    def calculate_ma(
        self, stock: Stock, window: int, days: int = None
    ) -> Optional[float]:
        """计算移动平均线"""
        days = days or window + 10
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)

        result = DailyData.objects.filter(
            stock=stock, date__gte=start_date, date__lte=end_date
        ).aggregate(avg_close=Avg("close"))

        if result["avg_close"]:
            return float(result["avg_close"])
        return None

    def calculate_ma_series(
        self, stock: Stock, window: int, limit: int = 50
    ) -> List[float]:
        """计算移动平均线序列"""
        data = DailyData.objects.filter(stock=stock).order_by("-date")[: window + limit]

        ma_values = []
        for i in range(len(data) - window + 1):
            window_data = data[i : i + window]
            ma = sum(float(d.close) for d in window_data) / window
            ma_values.append((window_data[0].date, ma))

        return ma_values[::-1]

    def get_stocks(self) -> List[Stock]:
        """获取策略关注的股票"""
        stock_codes = self.parameters.get("stock_codes", [])
        if stock_codes:
            return Stock.objects.filter(code__in=stock_codes, is_active=True)
        return Stock.objects.filter(is_active=True)[:20]

    def generate_signals(self) -> List[Dict]:
        """生成交易信号"""
        signals = []
        stocks = self.get_stocks()

        for stock in stocks:
            signal = self.analyze_stock(stock)
            if signal:
                signals.append(signal)

        return signals

    def analyze_stock(self, stock: Stock) -> Optional[Dict]:
        """分析单只股票"""
        ma_short = self.calculate_ma_series(stock, self.short_window)
        ma_long = self.calculate_ma_series(stock, self.long_window)

        if len(ma_short) < 2 or len(ma_long) < 2:
            return None

        short_current = ma_short[-1][1]
        short_prev = ma_short[-2][1]
        long_current = ma_long[-1][1]
        long_prev = ma_long[-2][1]

        current_date = ma_short[-1][0]

        crossover = None
        if short_prev <= long_prev and short_current > long_current:
            crossover = "golden_cross"
            signal_type = "buy"
            strength = min((short_current - long_current) / long_current * 10, 1.0)
            reason = f"金叉: 短期均线({self.short_window})上穿长期均线({self.long_window}), MA5={short_current:.2f}, MA20={long_current:.2f}"
        elif short_prev >= long_prev and short_current < long_current:
            crossover = "death_cross"
            signal_type = "sell"
            strength = min((long_current - short_current) / long_current * 10, 1.0)
            reason = f"死叉: 短期均线({self.short_window})下穿长期均线({self.long_window}), MA5={short_current:.2f}, MA20={long_current:.2f}"
        else:
            return None

        return {
            "stock": stock,
            "signal_type": signal_type,
            "strength": strength,
            "price": short_current,
            "reason": reason,
            "date": current_date,
            "indicators": {
                "ma_short": short_current,
                "ma_long": long_current,
                "crossover": crossover,
            },
        }

    def save_signal(self, signal_data: Dict) -> StrategySignal:
        """保存信号到数据库"""
        signal = StrategySignal.objects.create(
            strategy=self.strategy_instance,
            stock=signal_data["stock"],
            signal_type=signal_data["signal_type"],
            strength=signal_data["strength"],
            price=Decimal(str(signal_data["price"])),
            reason=signal_data["reason"],
        )
        return signal

    def run(self) -> List[StrategySignal]:
        """运行策略并保存信号"""
        signals_data = self.generate_signals()
        saved_signals = []

        for signal_data in signals_data:
            signal = self.save_signal(signal_data)
            saved_signals.append(signal)

        if saved_signals:
            self.strategy_instance.total_signals += len(saved_signals)
            self.strategy_instance.save()

        return saved_signals

    def get_performance_stats(self) -> Dict:
        """获取策略统计信息"""
        signals = StrategySignal.objects.filter(strategy=self.strategy_instance)

        buy_signals = signals.filter(signal_type="buy")
        sell_signals = signals.filter(signal_type="sell")

        return {
            "total_signals": signals.count(),
            "buy_signals": buy_signals.count(),
            "sell_signals": sell_signals.count(),
            "avg_strength": signals.aggregate(Avg("strength"))["strength__avg"] or 0,
        }


class BollingerBandsStrategy:
    """
    布林带策略

    策略逻辑:
    - 价格跌破下轨 -> 超卖信号 -> 买入
    - 价格突破上轨 -> 超买信号 -> 卖出
    """

    name = "布林带策略"
    version = "1.0.0"

    default_parameters = {
        "window": 20,
        "std_dev": 2,
        "stock_codes": [],
    }

    def __init__(self, strategy_instance: Strategy, parameters: Optional[Dict] = None):
        self.strategy_instance = strategy_instance
        self.parameters = {**self.default_parameters, **(parameters or {})}
        self.window = self.parameters["window"]
        self.std_dev = self.parameters["std_dev"]

    def calculate_bollinger_bands(self, stock: Stock) -> Optional[Dict]:
        """计算布林带"""
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=self.window + 50)

        data = DailyData.objects.filter(
            stock=stock, date__gte=start_date, date__lte=end_date
        ).order_by("-date")[: self.window + 1]

        if len(data) < self.window:
            return None

        closes = [float(d.close) for d in data]
        closes.reverse()

        middle = sum(closes) / len(closes)
        variance = sum((x - middle) ** 2 for x in closes) / len(closes)
        std = variance**0.5

        upper = middle + (self.std_dev * std)
        lower = middle - (self.std_dev * std)
        current_price = closes[-1]

        return {
            "upper": upper,
            "middle": middle,
            "lower": lower,
            "current": current_price,
            "date": data[0].date,
        }

    def generate_signals(self) -> List[Dict]:
        """生成交易信号"""
        signals = []
        stock_codes = self.parameters.get("stock_codes", [])

        if stock_codes:
            stocks = Stock.objects.filter(code__in=stock_codes, is_active=True)
        else:
            stocks = Stock.objects.filter(is_active=True)[:20]

        for stock in stocks:
            bb = self.calculate_bollinger_bands(stock)
            if not bb:
                continue

            if bb["current"] <= bb["lower"]:
                signals.append(
                    {
                        "stock": stock,
                        "signal_type": "buy",
                        "strength": 0.8,
                        "price": bb["current"],
                        "reason": f"价格({bb['current']:.2f})触及布林带下轨({bb['lower']:.2f})",
                    }
                )
            elif bb["current"] >= bb["upper"]:
                signals.append(
                    {
                        "stock": stock,
                        "signal_type": "sell",
                        "strength": 0.8,
                        "price": bb["current"],
                        "reason": f"价格({bb['current']:.2f})触及布林带上轨({bb['upper']:.2f})",
                    }
                )

        return signals


class RSIStrategy:
    """
    RSI相对强弱指标策略

    策略逻辑:
    - RSI < 30 -> 超卖 -> 买入
    - RSI > 70 -> 超买 -> 卖出
    """

    name = "RSI策略"
    version = "1.0.0"

    default_parameters = {
        "period": 14,
        "oversold": 30,
        "overbought": 70,
        "stock_codes": [],
    }

    def __init__(self, strategy_instance: Strategy, parameters: Optional[Dict] = None):
        self.strategy_instance = strategy_instance
        self.parameters = {**self.default_parameters, **(parameters or {})}
        self.period = self.parameters["period"]
        self.oversold = self.parameters["oversold"]
        self.overbought = self.parameters["overbought"]

    def calculate_rsi(self, stock: Stock) -> Optional[float]:
        """计算RSI"""
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=self.period + 50)

        data = list(
            DailyData.objects.filter(
                stock=stock, date__gte=start_date, date__lte=end_date
            ).order_by("date")[: self.period + 1]
        )

        if len(data) < self.period + 1:
            return None

        closes = [float(d.close) for d in data]
        changes = [closes[i] - closes[i - 1] for i in range(1, len(closes))]

        gains = [c if c > 0 else 0 for c in changes]
        losses = [-c if c < 0 else 0 for c in changes]

        avg_gain = sum(gains[: self.period]) / self.period
        avg_loss = sum(losses[: self.period]) / self.period

        for i in range(self.period, len(changes)):
            avg_gain = (avg_gain * (self.period - 1) + gains[i]) / self.period
            avg_loss = (avg_loss * (self.period - 1) + losses[i]) / self.period

        if avg_loss == 0:
            return 100

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    def generate_signals(self) -> List[Dict]:
        """生成交易信号"""
        signals = []
        stock_codes = self.parameters.get("stock_codes", [])

        if stock_codes:
            stocks = Stock.objects.filter(code__in=stock_codes, is_active=True)
        else:
            stocks = Stock.objects.filter(is_active=True)[:20]

        for stock in stocks:
            rsi = self.calculate_rsi(stock)
            if rsi is None:
                continue

            latest_data = (
                DailyData.objects.filter(stock=stock).order_by("-date").first()
            )
            if not latest_data:
                continue

            price = float(latest_data.close)

            if rsi < self.oversold:
                signals.append(
                    {
                        "stock": stock,
                        "signal_type": "buy",
                        "strength": (self.oversold - rsi) / self.oversold,
                        "price": price,
                        "reason": f"RSI({rsi:.2f})低于超卖线({self.oversold})",
                    }
                )
            elif rsi > self.overbought:
                signals.append(
                    {
                        "stock": stock,
                        "signal_type": "sell",
                        "strength": (rsi - self.overbought) / (100 - self.overbought),
                        "price": price,
                        "reason": f"RSI({rsi:.2f})高于超买线({self.overbought})",
                    }
                )

        return signals


def get_strategy_class(strategy_name: str):
    """根据策略名称获取策略类"""
    strategies = {
        "ma_crossover": MovingAverageCrossoverStrategy,
        "bollinger_bands": BollingerBandsStrategy,
        "rsi": RSIStrategy,
    }
    return strategies.get(strategy_name)
