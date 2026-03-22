"""
Backtesting Celery Tasks
异步执行回测任务
"""

import logging
from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def run_backtest_task(self, backtest_id: int, stock_codes: list = None):
    """
    异步运行回测任务

    Args:
        backtest_id: 回测记录ID
        stock_codes: 股票代码列表(可选)

    Returns:
        dict: 回测结果
    """
    from .models import Backtest
    from .engine import BacktestEngine

    try:
        backtest = Backtest.objects.select_related("strategy", "user").get(
            id=backtest_id
        )

        if backtest.status in ["running", "completed"]:
            logger.warning(f"回测 {backtest_id} 已在运行或已完成")
            return {
                "status": "skipped",
                "message": f"回测状态为 {backtest.status}",
                "backtest_id": backtest_id,
            }

        logger.info(f"开始执行回测任务: {backtest_id}")

        engine = BacktestEngine(backtest, stock_codes)
        metrics = engine.run()

        return {
            "status": "success",
            "backtest_id": backtest_id,
            "metrics": {
                "total_return": metrics.total_return,
                "sharpe_ratio": metrics.sharpe_ratio,
                "max_drawdown": metrics.max_drawdown,
                "win_rate": metrics.win_rate,
                "total_trades": metrics.total_trades,
                "winning_trades": metrics.winning_trades,
                "losing_trades": metrics.losing_trades,
                "profit_factor": metrics.profit_factor,
                "annual_return": metrics.annual_return,
                "volatility": metrics.volatility,
            },
            "equity_curve": engine.get_equity_curve()[-10:],
            "trade_history": engine.get_trade_history()[-20:],
        }

    except Backtest.DoesNotExist:
        logger.error(f"回测 {backtest_id} 不存在")
        return {
            "status": "error",
            "message": f"回测 {backtest_id} 不存在",
            "backtest_id": backtest_id,
        }

    except Exception as e:
        logger.error(f"回测 {backtest_id} 执行失败: {e}")

        try:
            backtest = Backtest.objects.get(id=backtest_id)
            backtest.status = "failed"
            backtest.error_message = str(e)
            backtest.save()
        except:
            pass

        raise self.retry(exc=e, countdown=60)


@shared_task(bind=True, max_retries=3)
def batch_backtest_task(self, backtest_ids: list, stock_codes: list = None):
    """
    批量回测任务

    Args:
        backtest_ids: 回测ID列表
        stock_codes: 股票代码列表(可选)

    Returns:
        dict: 批量回测结果
    """
    results = []

    for backtest_id in backtest_ids:
        try:
            result = run_backtest_task.delay(backtest_id, stock_codes)
            results.append(
                {
                    "backtest_id": backtest_id,
                    "task_id": result.id,
                    "status": "submitted",
                }
            )
        except Exception as e:
            results.append(
                {"backtest_id": backtest_id, "status": "error", "message": str(e)}
            )

    return {"status": "batch_submitted", "total": len(backtest_ids), "results": results}


@shared_task
def cleanup_old_backtests(days: int = 90):
    """
    清理旧的回测记录

    Args:
        days: 保留天数
    """
    from .models import Backtest

    cutoff_date = timezone.now() - timezone.timedelta(days=days)

    old_backtests = Backtest.objects.filter(
        created_at__lt=cutoff_date, status__in=["completed", "failed"]
    )

    count = old_backtests.count()
    old_backtests.delete()

    logger.info(f"清理了 {count} 条旧的回测记录")
    return {"deleted": count}


@shared_task
def get_backtest_result(backtest_id: int) -> dict:
    """
    获取回测结果

    Args:
        backtest_id: 回测ID

    Returns:
        dict: 回测结果
    """
    from .models import Backtest, BacktestTrade, BacktestEquity

    try:
        backtest = Backtest.objects.get(id=backtest_id)

        trades = BacktestTrade.objects.filter(backtest=backtest).order_by("datetime")
        equity = BacktestEquity.objects.filter(backtest=backtest).order_by("date")

        return {
            "status": "success",
            "backtest": {
                "id": backtest.id,
                "strategy_name": backtest.strategy.name,
                "start_date": backtest.start_date.isoformat(),
                "end_date": backtest.end_date.isoformat(),
                "initial_capital": float(backtest.initial_capital),
                "final_capital": float(backtest.final_capital)
                if backtest.final_capital
                else None,
                "total_return": backtest.total_return,
                "sharpe_ratio": backtest.sharpe_ratio,
                "max_drawdown": backtest.max_drawdown,
                "win_rate": backtest.win_rate,
                "total_trades": backtest.total_trades,
                "status": backtest.status,
                "created_at": backtest.created_at.isoformat(),
                "completed_at": backtest.completed_at.isoformat()
                if backtest.completed_at
                else None,
            },
            "trades": [
                {
                    "datetime": t.datetime.isoformat(),
                    "stock_code": t.stock.code,
                    "signal_type": t.signal_type,
                    "price": float(t.price),
                    "quantity": t.quantity,
                    "commission": float(t.commission),
                }
                for t in trades
            ],
            "equity_curve": [
                {
                    "date": e.date.isoformat(),
                    "total_value": float(e.total_value),
                    "cash": float(e.cash),
                    "positions_value": float(e.positions_value),
                    "daily_return": e.daily_return,
                }
                for e in equity
            ],
        }

    except Backtest.DoesNotExist:
        return {"status": "error", "message": f"回测 {backtest_id} 不存在"}
