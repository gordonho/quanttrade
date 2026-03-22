from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """扩展用户模型"""
    api_key = models.CharField(max_length=64, blank=True, null=True)
    api_secret = models.CharField(max_length=128, blank=True, null=True)
    is_active_strategy = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users'


class APIKey(models.Model):
    """券商API Key管理"""
    BROKER_CHOICES = [
        ('huatai', '华泰证券'),
        ('citic', '中信证券'),
        ('xueqiu', '雪球'),
        ('yahoo', 'Yahoo'),
        ('other', '其他'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='api_keys')
    name = models.CharField(max_length=50, verbose_name='名称')
    key = models.CharField(max_length=64, verbose_name='API Key')
    secret = models.CharField(max_length=128, blank=True, null=True, verbose_name='Secret')
    broker = models.CharField(max_length=20, choices=BROKER_CHOICES, verbose_name='券商')
    is_active = models.BooleanField(default=True, verbose_name='是否激活')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'api_keys'
        verbose_name = 'API Key'
        verbose_name_plural = 'API Keys'
