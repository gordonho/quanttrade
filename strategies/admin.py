from django.contrib import admin
from .models import Strategy, StrategySignal, StrategyParameter

@admin.register(Strategy)
class StrategyAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'status', 'total_signals', 'win_rate']
    list_filter = ['status']

@admin.register(StrategySignal)
class StrategySignalAdmin(admin.ModelAdmin):
    list_display = ['strategy', 'stock', 'signal_type', 'strength', 'price', 'created_at']

@admin.register(StrategyParameter)
class StrategyParameterAdmin(admin.ModelAdmin):
    list_display = ['strategy', 'name', 'value']
