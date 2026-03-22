from rest_framework import serializers
from .models import Portfolio, PortfolioHistory, PortfolioAllocation


class PortfolioAllocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortfolioAllocation
        fields = ['id', 'name', 'target_percent', 'current_percent']


class PortfolioHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PortfolioHistory
        fields = ['id', 'date', 'total_value', 'cash', 'positions_value', 'daily_return']


class PortfolioSerializer(serializers.ModelSerializer):
    allocations = PortfolioAllocationSerializer(many=True, read_only=True)
    history = PortfolioHistorySerializer(many=True, read_only=True)
    
    class Meta:
        model = Portfolio
        fields = ['id', 'name', 'description', 'total_capital', 'available_cash', 
                  'frozen_cash', 'created_at', 'updated_at', 'allocations', 'history']
        read_only_fields = ['id', 'created_at', 'updated_at']
