from rest_framework import serializers
from .models import Order, Trade, Position


class TradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trade
        fields = [
            "id",
            "order",
            "stock",
            "filled_quantity",
            "filled_price",
            "commission",
            "filled_at",
        ]
        read_only_fields = ["id", "filled_at"]


class OrderSerializer(serializers.ModelSerializer):
    trades = TradeSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "user",
            "strategy",
            "stock",
            "order_type",
            "direction",
            "price",
            "quantity",
            "status",
            "broker_order_id",
            "filled_quantity",
            "filled_price",
            "filled_amount",
            "created_at",
            "updated_at",
            "filled_at",
            "trades",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "filled_at"]


class PositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Position
        fields = [
            "id",
            "user",
            "strategy",
            "stock",
            "quantity",
            "avg_cost",
            "market_value",
            "profit_loss",
            "profit_loss_percent",
            "updated_at",
        ]
        read_only_fields = ["id", "updated_at"]
