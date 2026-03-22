from rest_framework import serializers
from .models import Backtest, BacktestTrade, BacktestEquity


class BacktestEquitySerializer(serializers.ModelSerializer):
    class Meta:
        model = BacktestEquity
        fields = [
            "id",
            "backtest",
            "date",
            "total_value",
            "cash",
            "positions_value",
            "daily_return",
        ]
        read_only_fields = ["id"]


class BacktestTradeSerializer(serializers.ModelSerializer):
    stock_code = serializers.CharField(source="stock.code", read_only=True)

    class Meta:
        model = BacktestTrade
        fields = [
            "id",
            "backtest",
            "stock",
            "stock_code",
            "signal_type",
            "price",
            "quantity",
            "commission",
            "datetime",
        ]
        read_only_fields = ["id"]


class BacktestSerializer(serializers.ModelSerializer):
    strategy_name = serializers.CharField(source="strategy.name", read_only=True)
    trades = BacktestTradeSerializer(many=True, read_only=True)
    equity_curve = BacktestEquitySerializer(many=True, read_only=True)

    class Meta:
        model = Backtest
        fields = [
            "id",
            "user",
            "strategy",
            "strategy_name",
            "start_date",
            "end_date",
            "initial_capital",
            "commission",
            "slippage",
            "final_capital",
            "total_return",
            "sharpe_ratio",
            "max_drawdown",
            "win_rate",
            "total_trades",
            "status",
            "error_message",
            "created_at",
            "completed_at",
            "trades",
            "equity_curve",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "final_capital",
            "total_return",
            "sharpe_ratio",
            "max_drawdown",
            "win_rate",
            "total_trades",
        ]
