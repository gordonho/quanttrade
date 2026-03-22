from django.db import models
from django.conf import settings
from strategies.models import Strategy
from market_data.models import Stock


class Order(models.Model):
    """订单"""
    ORDER_TYPES = [
        ('market', '市价'),
        ('limit', '限价'),
    ]
    
    DIRECTIONS = [
        ('buy', '买入'),
        ('sell', '卖出'),
    ]
    
    STATUS_CHOICES = [
        ('pending', '待成交'),
        ('partial', '部分成交'),
        ('filled', '全部成交'),
        ('cancelled', '已撤销'),
        ('rejected', '已拒绝'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    strategy = models.ForeignKey(Strategy, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='orders')
    
    order_type = models.CharField(max_length=10, choices=ORDER_TYPES, verbose_name='订单类型')
    direction = models.CharField(max_length=10, choices=DIRECTIONS, verbose_name='方向')
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='限价')
    quantity = models.IntegerField(verbose_name='委托数量')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='状态')
    
    # 券商返回信息
    broker_order_id = models.CharField(max_length=64, null=True, blank=True, verbose_name='券商订单ID')
    
    # 成交信息
    filled_quantity = models.IntegerField(default=0, verbose_name='已成交数量')
    filled_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='成交价格')
    filled_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='成交金额')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    filled_at = models.DateTimeField(null=True, blank=True, verbose_name='成交时间')

    class Meta:
        db_table = 'orders'
        verbose_name = '订单'
        verbose_name_plural = '订单'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['broker_order_id']),
        ]

    def __str__(self):
        return f"{self.stock.code} {self.get_direction_display()} {self.quantity}@{self.price or '市价'}"


class Trade(models.Model):
    """成交记录"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='trades')
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='trades')
    
    filled_quantity = models.IntegerField(verbose_name='成交数量')
    filled_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='成交价格')
    commission = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='手续费')
    filled_at = models.DateTimeField(auto_now_add=True, verbose_name='成交时间')

    class Meta:
        db_table = 'trades'
        verbose_name = '成交'
        verbose_name_plural = '成交'
        ordering = ['-filled_at']

    def __str__(self):
        return f"{self.stock.code} {self.filled_quantity}@{self.filled_price}"


class Position(models.Model):
    """持仓"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='positions')
    strategy = models.ForeignKey(Strategy, on_delete=models.SET_NULL, null=True, blank=True, related_name='positions')
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='positions')
    
    quantity = models.IntegerField(default=0, verbose_name='持仓数量')
    avg_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='平均成本')
    market_value = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='市值')
    profit_loss = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='浮动盈亏')
    profit_loss_percent = models.FloatField(default=0, verbose_name='盈亏比例')
    
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'positions'
        verbose_name = '持仓'
        verbose_name_plural = '持仓'
        unique_together = ['user', 'strategy', 'stock']

    def __str__(self):
        return f"{self.stock.code} {self.quantity}股"
    
    def update_market_value(self, current_price):
        """更新市值和盈亏"""
        self.market_value = current_price * self.quantity
        self.profit_loss = self.market_value - (self.avg_cost * self.quantity)
        if self.avg_cost > 0:
            self.profit_loss_percent = (self.market_value - (self.avg_cost * self.quantity)) / (self.avg_cost * self.quantity) * 100
        self.save()
