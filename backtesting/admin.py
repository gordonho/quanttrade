from django.contrib import admin
from .models import Backtest, BacktestTrade, BacktestEquity

@admin.register(Backtest)
class BacktestAdmin(admin.ModelAdmin):
    list_display = ['id', 'strategy', 'start_date', 'end_date', 'status', 'total_return']
    list_filter = ['status']

@admin.register(BacktestTrade)
class BacktestTradeAdmin(admin.ModelAdmin):
    list_display = ['id', 'backtest', 'stock', 'signal_type', 'price', 'quantity']

@admin.register(BacktestEquity)
class BacktestEquityAdmin(admin.ModelAdmin):
    list_display = ['id', 'backtest', 'date', 'total_value']
