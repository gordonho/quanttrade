from rest_framework import serializers
from .models import Stock, DailyData


class DailyDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyData
        fields = [
            'id', 'stock', 'date', 'open', 'high', 'low', 'close',
            'volume', 'amount', 'turnover_rate'
        ]
        read_only_fields = ['id']


class StockSerializer(serializers.ModelSerializer):
    daily_data = DailyDataSerializer(many=True, read_only=True)

    class Meta:
        model = Stock
        fields = [
            'id', 'code', 'name', 'industry', 'market', 'list_date',
            'is_active', 'created_at', 'updated_at', 'daily_data'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
