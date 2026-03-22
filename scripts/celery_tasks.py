"""
Celery异步任务 - 数据采集和策略执行
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'quanttrade.settings')
django.setup()

from celery import shared_task
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@shared_task
def collect_stock_list():
    """采集股票列表"""
    from scripts.data_collector import get_stock_list
    try:
        count = get_stock_list()
        logger.info(f"Stock list collected: {count} stocks")
        return {"success": True, "count": count}
    except Exception as e:
        logger.error(f"Failed to collect stock list: {e}")
        return {"success": False, "error": str(e)}


@shared_task
def collect_daily_data(symbol, start_date=None, end_date=None):
    """采集日线数据"""
    from scripts.data_collector import get_daily_data
    try:
        count = get_daily_data(symbol, start_date, end_date)
        logger.info(f"Daily data collected for {symbol}: {count} records")
        return {"success": True, "symbol": symbol, "count": count}
    except Exception as e:
        logger.error(f"Failed to collect daily data for {symbol}: {e}")
        return {"success": False, "error": str(e)}


@shared_task
def collect_realtime_quotes():
    """采集实时行情"""
    from scripts.data_collector import get_all_realtime_quotes
    try:
        get_all_realtime_quotes()
        logger.info("Realtime quotes collected")
        return {"success": True}
    except Exception as e:
        logger.error(f"Failed to collect realtime quotes: {e}")
        return {"success": False, "error": str(e)}


@shared_task
def run_strategy(strategy_id):
    """运行策略生成信号"""
    from strategies.models import Strategy
    from strategies.sample_strategy import run_ma_crossover
    
    try:
        strategy = Strategy.objects.get(id=strategy_id)
        if strategy.status != 'active':
            return {"success": False, "error": "Strategy is not active"}
        
        # 获取需要处理的股票列表
        from market_data.models import Stock
        stocks = Stock.objects.filter(is_active=True)[:100]  # 限制数量
        
        signals = []
        for stock in stocks:
            try:
                signal = run_ma_crossover(stock.code, strategy.parameters)
                if signal:
                    signals.append(signal)
            except Exception as e:
                logger.error(f"Error running strategy for {stock.code}: {e}")
                continue
        
        logger.info(f"Strategy {strategy_id} generated {len(signals)} signals")
        return {"success": True, "signals_count": len(signals)}
        
    except Strategy.DoesNotExist:
        return {"success": False, "error": "Strategy not found"}
    except Exception as e:
        logger.error(f"Failed to run strategy {strategy_id}: {e}")
        return {"success": False, "error": str(e)}


@shared_task
def execute_trade(order_id):
    """执行交易订单"""
    from trading.broker import Broker
    from trading.models import Order
    from django.contrib.auth import get_user_model
    
    try:
        order = Order.objects.get(id=order_id)
        user = order.user
        
        broker = Broker(user=user, strategy=order.strategy)
        broker.place_order(
            stock=order.stock,
            direction=order.direction,
            quantity=order.quantity,
            order_type=order.order_type,
            price=order.price
        )
        
        logger.info(f"Order {order_id} executed")
        return {"success": True}
        
    except Order.DoesNotExist:
        return {"success": False, "error": "Order not found"}
    except Exception as e:
        logger.error(f"Failed to execute order {order_id}: {e}")
        return {"success": False, "error": str(e)}


@shared_task
def update_positions():
    """更新所有持仓市值"""
    from trading.models import Position
    from market_data.models import RealtimeQuote
    
    try:
        positions = Position.objects.filter(quantity__gt=0)
        updated = 0
        
        for position in positions:
            try:
                quote = RealtimeQuote.objects.get(stock=position.stock)
                position.update_market_value(quote.price)
                updated += 1
            except RealtimeQuote.DoesNotExist:
                continue
        
        logger.info(f"Updated {updated} positions")
        return {"success": True, "updated": updated}
        
    except Exception as e:
        logger.error(f"Failed to update positions: {e}")
        return {"success": False, "error": str(e)}


@shared_task
def daily_task():
    """每日定时任务"""
    logger.info("Running daily task...")
    
    # 1. 采集股票列表
    collect_stock_list.delay()
    
    # 2. 采集实时行情
    collect_realtime_quotes.delay()
    
    # 3. 更新持仓
    update_positions.delay()
    
    return {"success": True, "message": "Daily tasks scheduled"}
