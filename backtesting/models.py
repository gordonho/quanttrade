from django.db import models
from django.conf import settings
from strategies.models import Strategy
from market_data.models import Stock


class Backtest(models.Model):
    """回测记录"""
    STATUS_CHOICES = [
        ('pending', '待运行'),
        ('running', '运行中'),
        ('completed', '完成'),
        ('failed', '失败'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='backtests')
    strategy = models.ForeignKey(Strategy, on_delete=models.CASCADE, related_name='backtests')
    
    # 回测参数
    start_date = models.DateField(verbose_name='开始日期')
    end_date = models.DateField(verbose_name='结束日期')
    initial_capital = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='初始资金')
    commission = models.FloatField(default=0.0003, verbose_name='手续费率')
    slippage = models.FloatField(default=0.001, verbose_name='滑点')
    
    # 回测结果
    final_capital = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, verbose_name='最终资金')
    total_return = models.FloatField(null=True, blank=True, verbose_name='总收益率')
    sharpe_ratio = models.FloatField(null=True, blank=True, verbose_name='夏普比率')
    max_drawdown = models.FloatField(null=True, blank=True, verbose_name='最大回撤')
    win_rate = models.FloatField(null=True, blank=True, verbose_name='胜率')
    total_trades = models.PositiveIntegerField(null=True, blank=True, verbose_name='总交易次数')
    
    # 状态
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='状态')
    error_message = models.TextField(blank=True, verbose_name='错误信息')
    
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='完成时间')

    class Meta:
        db_table = 'backtests'
        verbose_name = '回测'
        verbose_name_plural = '回测'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.strategy.name} {self.start_date} ~ {self.end_date}"


class BacktestTrade(models.Model):
    """回测交易记录"""
    SIGNAL_TYPES = [
        ('buy', '买入'),
        ('sell', '卖出'),
    ]
    
    backtest = models.ForeignKey(Backtest, on_delete=models.CASCADE, related_name='trades')
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    signal_type = models.CharField(max_length=10, choices=SIGNAL_TYPES, verbose_name='交易类型')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='价格')
    quantity = models.IntegerField(verbose_name='数量')
    commission = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='手续费')
    datetime = models.DateTimeField(verbose_name='时间')
    
    class Meta:
        db_table = 'backtest_trades'
        verbose_name = '回测交易'
        verbose_name_plural = '回测交易'
        ordering = ['datetime']

    def __str__(self):
        return f"{self.backtest.id} {self.stock.code} {self.get_signal_type_display()} {self.quantity}"


class BacktestEquity(models.Model):
    """回测权益曲线"""
    backtest = models.ForeignKey(Backtest, on_delete=models.CASCADE, related_name='equity_curve')
    date = models.DateField(verbose_name='日期')
    total_value = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='总市值')
    cash = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='现金')
    positions_value = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='持仓市值')
    daily_return = models.FloatField(verbose_name='日收益率')
    
    class Meta:
        db_table = 'backtest_equity'
        verbose_name = '回测权益'
        verbose_name_plural = '回测权益'
        unique_together = ['backtest', 'date']
        indexes = [
            models.Index(fields=['date']),
        ]

    def __str__(self):
        return f"{self.backtest.id} {self.date} {self.total_value}"
