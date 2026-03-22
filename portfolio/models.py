from django.db import models
from django.conf import settings


class Portfolio(models.Model):
    """投资组合"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='portfolios')
    name = models.CharField(max_length=100, verbose_name='组合名称')
    description = models.TextField(blank=True, verbose_name='描述')
    
    total_capital = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='总资金')
    available_cash = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='可用资金')
    frozen_cash = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='冻结资金')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'portfolios'
        verbose_name = '投资组合'
        verbose_name_plural = '投资组合'

    def __str__(self):
        return self.name
    
    @property
    def positions_value(self):
        """持仓市值"""
        from trading.models import Position
        positions = Position.objects.filter(user=self.user)
        return sum(p.market_value for p in positions)
    
    @property
    def total_value(self):
        """总市值"""
        return self.available_cash + self.frozen_cash + self.positions_value


class PortfolioHistory(models.Model):
    """组合历史净值"""
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name='history')
    date = models.DateField(verbose_name='日期')
    total_value = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='总市值')
    cash = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='现金')
    positions_value = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='持仓市值')
    daily_return = models.FloatField(default=0, verbose_name='日收益率')
    
    class Meta:
        db_table = 'portfolio_history'
        verbose_name = '组合历史'
        verbose_name_plural = '组合历史'
        unique_together = ['portfolio', 'date']
        indexes = [
            models.Index(fields=['date']),
        ]

    def __str__(self):
        return f"{self.portfolio.name} {self.date}"


class PortfolioAllocation(models.Model):
    """资产配置"""
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name='allocations')
    name = models.CharField(max_length=50, verbose_name='配置名称')
    target_percent = models.FloatField(default=0, verbose_name='目标比例')
    current_percent = models.FloatField(default=0, verbose_name='当前比例')
    
    class Meta:
        db_table = 'portfolio_allocation'
        verbose_name = '资产配置'
        verbose_name_plural = '资产配置'

    def __str__(self):
        return f"{self.portfolio.name} - {self.name}"
