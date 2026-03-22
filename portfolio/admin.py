from django.contrib import admin
from .models import Portfolio, PortfolioHistory, PortfolioAllocation

@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'total_capital', 'available_cash']

@admin.register(PortfolioHistory)
class PortfolioHistoryAdmin(admin.ModelAdmin):
    list_display = ['portfolio', 'date', 'total_value', 'daily_return']

@admin.register(PortfolioAllocation)
class PortfolioAllocationAdmin(admin.ModelAdmin):
    list_display = ['portfolio', 'name', 'target_percent', 'current_percent']
