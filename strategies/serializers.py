from rest_framework import serializers
from .models import Strategy, StrategySignal, StrategyParameter


class StrategySignalSerializer(serializers.ModelSerializer):
    class Meta:
        model = StrategySignal
        fields = [
            'id', 'strategy', 'stock', 'signal_type', 'strength',
            'price', 'reason', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class StrategyParameterSerializer(serializers.ModelSerializer):
    class Meta:
        model = StrategyParameter
        fields = [
            'id', 'strategy', 'name', 'value', 'default_value',
            'description'
        ]
        read_only_fields = ['id']


class StrategySerializer(serializers.ModelSerializer):
    signals = StrategySignalSerializer(many=True, read_only=True)
    params = StrategyParameterSerializer(many=True, read_only=True)

    class Meta:
        model = Strategy
        fields = [
            'id', 'user', 'name', 'description', 'code', 'language',
            'parameters', 'status', 'total_signals', 'win_rate',
            'created_at', 'updated_at', 'started_at', 'signals', 'params'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'total_signals', 'win_rate']
