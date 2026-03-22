from django.db import models


class Stock(models.Model):
    """股票基本信息"""
    MARKET_CHOICES = [
        ('SH', '上海证券交易所'),
        ('SZ', '深圳证券交易所'),
        ('BJ', '北京证券交易所'),
    ]
    
    code = models.CharField(max_length=10, unique=True, verbose_name='股票代码')
    name = models.CharField(max_length=50, verbose_name='股票名称')
    industry = models.CharField(max_length=50, blank=True, verbose_name='所属行业')
    market = models.CharField(max_length=2, choices=MARKET_CHOICES, verbose_name='市场')
    list_date = models.DateField(null=True, blank=True, verbose_name='上市日期')
    is_active = models.BooleanField(default=True, verbose_name='是否交易')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'stocks'
        verbose_name = '股票'
        verbose_name_plural = '股票'
        indexes = [
            models.Index(fields=['industry']),
            models.Index(fields=['market']),
        ]

    def __str__(self):
        return f"{self.code} {self.name}"


class DailyData(models.Model):
    """日线数据"""
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='daily_data')
    date = models.DateField(verbose_name='日期')
    open = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='开盘价')
    high = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='最高价')
    low = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='最低价')
    close = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='收盘价')
    volume = models.BigIntegerField(verbose_name='成交量')
    amount = models.DecimalField(max_digits=20, decimal_places=2, verbose_name='成交额')
    turnover_rate = models.FloatField(null=True, blank=True, verbose_name='换手率')
    
    class Meta:
        db_table = 'daily_data'
        verbose_name = '日线数据'
        verbose_name_plural = '日线数据'
        unique_together = ['stock', 'date']
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['stock', 'date']),
        ]

    def __str__(self):
        return f"{self.stock.code} {self.date}"


class MinuteData(models.Model):
    """分钟线数据"""
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='minute_data')
    datetime = models.DateTimeField(verbose_name='时间')
    open = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='开盘价')
    high = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='最高价')
    low = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='最低价')
    close = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='收盘价')
    volume = models.BigIntegerField(verbose_name='成交量')
    
    class Meta:
        db_table = 'minute_data'
        verbose_name = '分钟线数据'
        verbose_name_plural = '分钟线数据'
        unique_together = ['stock', 'datetime']
        indexes = [
            models.Index(fields=['datetime']),
            models.Index(fields=['stock', 'datetime']),
        ]

    def __str__(self):
        return f"{self.stock.code} {self.datetime}"


class RealtimeQuote(models.Model):
    """实时行情"""
    stock = models.OneToOneField(Stock, on_delete=models.CASCADE, related_name='realtime_quote')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='当前价')
    change = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='涨跌额')
    change_percent = models.FloatField(verbose_name='涨跌幅')
    volume = models.BigIntegerField(verbose_name='成交量')
    amount = models.DecimalField(max_digits=20, decimal_places=2, verbose_name='成交额')
    open_today = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='今开')
    high = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='最高')
    low = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='最低')
    close_yesterday = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='昨收')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'realtime_quotes'
        verbose_name = '实时行情'
        verbose_name_plural = '实时行情'

    def __str__(self):
        return f"{self.stock.code} {self.price}"
