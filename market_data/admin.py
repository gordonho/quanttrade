from django.contrib import admin
from .models import Stock, DailyData, MinuteData, RealtimeQuote

@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'industry', 'market', 'is_active']
    search_fields = ['code', 'name']

@admin.register(DailyData)
class DailyDataAdmin(admin.ModelAdmin):
    list_display = ['stock', 'date', 'open', 'high', 'low', 'close', 'volume']

@admin.register(MinuteData)
class MinuteDataAdmin(admin.ModelAdmin):
    list_display = ['stock', 'datetime', 'close', 'volume']

@admin.register(RealtimeQuote)
class RealtimeQuoteAdmin(admin.ModelAdmin):
    list_display = ['stock', 'price', 'change', 'change_percent']
