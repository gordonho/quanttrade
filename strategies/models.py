from django.db import models
from django.conf import settings


class Strategy(models.Model):
    """量化策略"""
    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('active', '运行中'),
        ('stopped', '已停止'),
        ('archived', '已归档'),
    ]
    
    LANGUAGE_CHOICES = [
        ('python', 'Python'),
        ('javascript', 'JavaScript'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='strategies')
    name = models.CharField(max_length=100, verbose_name='策略名称')
    description = models.TextField(blank=True, verbose_name='策略描述')
    code = models.TextField(verbose_name='策略代码')
    language = models.CharField(max_length=20, choices=LANGUAGE_CHOICES, default='python', verbose_name='语言')
    parameters = models.JSONField(default=dict, verbose_name='策略参数')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name='状态')
    
    # 统计信息
    total_signals = models.PositiveIntegerField(default=0, verbose_name='信号总数')
    win_rate = models.FloatField(default=0, verbose_name='胜率')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    started_at = models.DateTimeField(null=True, blank=True, verbose_name='启动时间')

    class Meta:
        db_table = 'strategies'
        verbose_name = '策略'
        verbose_name_plural = '策略'
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"


class StrategySignal(models.Model):
    """策略信号"""
    SIGNAL_TYPES = [
        ('buy', '买入'),
        ('sell', '卖出'),
        ('hold', '持有'),
    ]
    
    strategy = models.ForeignKey(Strategy, on_delete=models.CASCADE, related_name='signals')
    stock = models.ForeignKey('market_data.Stock', on_delete=models.CASCADE, related_name='signals')
    signal_type = models.CharField(max_length=10, choices=SIGNAL_TYPES, verbose_name='信号类型')
    strength = models.FloatField(default=1.0, verbose_name='信号强度 0-1')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='价格')
    reason = models.TextField(blank=True, verbose_name='信号原因')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'strategy_signals'
        verbose_name = '策略信号'
        verbose_name_plural = '策略信号'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['strategy', 'created_at']),
        ]

    def __str__(self):
        return f"{self.strategy.name} {self.stock.code} {self.get_signal_type_display()} {self.price}"


class StrategyParameter(models.Model):
    """策略参数配置"""
    strategy = models.ForeignKey(Strategy, on_delete=models.CASCADE, related_name='params')
    name = models.CharField(max_length=50, verbose_name='参数名')
    value = models.CharField(max_length=100, verbose_name='参数值')
    default_value = models.CharField(max_length=100, verbose_name='默认值')
    description = models.CharField(max_length=200, blank=True, verbose_name='描述')
    
    class Meta:
        db_table = 'strategy_parameters'
        verbose_name = '策略参数'
        verbose_name_plural = '策略参数'
        unique_together = ['strategy', 'name']

    def __str__(self):
        return f"{self.strategy.name}.{self.name} = {self.value}"
