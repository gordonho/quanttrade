from django.contrib import admin
from .models import Order, Trade, Position

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'stock', 'direction', 'quantity', 'status', 'created_at']
    list_filter = ['status', 'direction']

@admin.register(Trade)
class TradeAdmin(admin.ModelAdmin):
    list_display = ['id', 'stock', 'filled_quantity', 'filled_price', 'filled_at']

@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ['id', 'stock', 'quantity', 'avg_cost', 'market_value']
