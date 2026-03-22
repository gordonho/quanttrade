"""
模拟券商交易服务 - 用于模拟交易/回测
"""
from decimal import Decimal
from datetime import datetime
from typing import Optional
from trading.models import Order, Position, Trade


class Broker:
    """模拟券商"""
    
    def __init__(self, user, strategy=None, commission_rate=0.0003):
        self.user = user
        self.strategy = strategy
        self.commission_rate = commission_rate
    
    def place_order(self, stock, direction, quantity, order_type='market', price=None) -> Order:
        """下单"""
        order = Order.objects.create(
            user=self.user,
            strategy=self.strategy,
            stock=stock,
            order_type=order_type,
            direction=direction,
            price=price,
            quantity=quantity,
            status='pending'
        )
        
        # 如果是市价单，立即成交
        if order_type == 'market':
            self._fill_order(order)
        
        return order
    
    def _fill_order(self, order: Order):
        """成交订单"""
        # 获取当前价格 (这里简化处理，实际应该获取实时价格)
        from market_data.models import RealtimeQuote
        try:
            quote = RealtimeQuote.objects.get(stock=order.stock)
            current_price = quote.price
        except RealtimeQuote.DoesNotExist:
            # 如果没有实时行情，使用默认价格
            current_price = Decimal('10.00')
        
        # 计算成交金额和手续费
        filled_amount = current_price * order.quantity
        commission = filled_amount * Decimal(str(self.commission_rate))
        
        # 更新订单状态
        order.status = 'filled'
        order.filled_quantity = order.quantity
        order.filled_price = current_price
        order.filled_amount = filled_amount
        order.filled_at = datetime.now()
        order.save()
        
        # 创建成交记录
        Trade.objects.create(
            order=order,
            stock=order.stock,
            filled_quantity=order.quantity,
            filled_price=current_price,
            commission=commission
        )
        
        # 更新持仓
        self._update_position(order, current_price)
    
    def _update_position(self, order: Order, price: Decimal):
        """更新持仓"""
        position, created = Position.objects.get_or_create(
            user=self.user,
            strategy=self.strategy,
            stock=order.stock,
            defaults={'quantity': 0, 'avg_cost': Decimal('0')}
        )
        
        if order.direction == 'buy':
            # 买入 - 增加持仓
            total_cost = position.avg_cost * position.quantity + price * order.filled_quantity
            position.quantity += order.filled_quantity
            if position.quantity > 0:
                position.avg_cost = total_cost / position.quantity
        else:
            # 卖出 - 减少持仓
            position.quantity -= order.filled_quantity
            if position.quantity == 0:
                position.avg_cost = Decimal('0')
        
        # 更新市值
        position.market_value = price * position.quantity
        if position.quantity > 0:
            position.profit_loss = position.market_value - (position.avg_cost * position.quantity)
            position.profit_loss_percent = float(position.profit_loss / (position.avg_cost * position.quantity) * 100)
        
        position.save()
    
    def get_positions(self):
        """获取所有持仓"""
        return Position.objects.filter(user=self.user, strategy=self.strategy, quantity__gt=0)
    
    def cancel_order(self, order_id: int) -> bool:
        """撤单"""
        try:
            order = Order.objects.get(id=order_id, user=self.user)
            if order.status in ['pending', 'partial']:
                order.status = 'cancelled'
                order.save()
                return True
            return False
        except Order.DoesNotExist:
            return False
