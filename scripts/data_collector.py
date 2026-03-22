"""
市场数据采集脚本
使用 AkShare 获取A股数据
"""
import os
import sys
import django
from datetime import datetime, timedelta

# 设置Django环境
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'quanttrade.settings')
django.setup()

import akshare as ak
from decimal import Decimal
from market_data.models import Stock, DailyData, RealtimeQuote


def get_stock_list():
    """获取A股股票列表"""
    print("获取股票列表...")
    df = ak.stock_info_a_code_name()
    stocks = []
    for _, row in df.iterrows():
        code = row['code']
        # 判断市场
        if code.startswith('6'):
            market = 'SH'
        elif code.startswith('000') or code.startswith('001'):
            market = 'SZ'
        elif code.startswith('300'):
            market = 'SZ'
        elif code.startswith('8') or code.startswith('4'):
            market = 'BJ'
        else:
            market = 'SZ'
        
        stocks.append({
            'code': code,
            'name': row['name'],
            'market': market,
        })
    
    # 批量创建/更新
    for s in stocks:
        Stock.objects.update_or_create(
            code=s['code'],
            defaults=s
        )
    
    print(f"股票列表更新完成，共 {len(stocks)} 只")
    return len(stocks)


def get_daily_data(symbol, start_date=None, end_date=None):
    """
    获取日线数据
    symbol: 股票代码，如 '000001'
    """
    if start_date is None:
        start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
    if end_date is None:
        end_date = datetime.now().strftime('%Y%m%d')
    
    try:
        df = ak.stock_zh_a_hist(symbol=symbol, period="daily", 
                                start_date=start_date, end_date=end_date)
        
        stock = Stock.objects.get(code=symbol)
        
        for _, row in df.iterrows():
            date = datetime.strptime(row['日期'], '%Y-%m-%d').date()
            
            DailyData.objects.update_or_create(
                stock=stock,
                date=date,
                defaults={
                    'open': Decimal(str(row['开盘'])),
                    'high': Decimal(str(row['最高'])),
                    'low': Decimal(str(row['最低'])),
                    'close': Decimal(str(row['收盘'])),
                    'volume': int(row['成交量']),
                    'amount': Decimal(str(row['成交额'])),
                    'turnover_rate': float(row['振幅'].replace('%', '')) if '振幅' in row else None,
                }
            )
        
        print(f"获取 {symbol} 日线数据成功，共 {len(df)} 条")
        return len(df)
        
    except Exception as e:
        print(f"获取 {symbol} 日线数据失败: {e}")
        return 0


def get_realtime_quote(symbol):
    """
    获取实时行情
    """
    try:
        df = ak.stock_zh_a_spot_em()
        stock_info = df[df['代码'] == symbol]
        
        if stock_info.empty:
            return None
        
        row = stock_info.iloc[0]
        stock = Stock.objects.get(code=symbol)
        
        quote, _ = RealtimeQuote.objects.update_or_create(
            stock=stock,
            defaults={
                'price': Decimal(str(row['最新价'])) if row['最新价'] != '--' else Decimal('0'),
                'change': Decimal(str(row['涨跌幅'])) if row['涨跌幅'] != '--' else Decimal('0'),
                'change_percent': float(row['涨跌幅'].replace('%', '')) if row['涨跌幅'] != '--' else 0,
                'volume': int(row['成交量'].replace('万', '')) * 10000 if isinstance(row['成交量'], str) else row['成交量'],
                'amount': Decimal(str(row['成交额'].replace('亿', ''))) * 100000000 if isinstance(row['成交额'], str) else row['成交额'],
                'open_today': Decimal(str(row['今开'])) if row['今开'] != '--' else Decimal('0'),
                'high': Decimal(str(row['最高'])) if row['最高'] != '--' else Decimal('0'),
                'low': Decimal(str(row['最低'])) if row['最低'] != '--' else Decimal('0'),
                'close_yesterday': Decimal(str(row['昨收'])) if row['昨收'] != '--' else Decimal('0'),
            }
        )
        
        print(f"获取 {symbol} 实时行情成功")
        return quote
        
    except Exception as e:
        print(f"获取 {symbol} 实时行情失败: {e}")
        return None


def get_all_realtime_quotes():
    """获取所有股票实时行情"""
    print("获取实时行情...")
    try:
        df = ak.stock_zh_a_spot_em()
        
        for _, row in df.iterrows():
            code = row['代码']
            try:
                stock = Stock.objects.get(code=code)
                
                RealtimeQuote.objects.update_or_create(
                    stock=stock,
                    defaults={
                        'price': Decimal(str(row['最新价'])) if row['最新价'] != '--' else Decimal('0'),
                        'change': Decimal(str(row['涨跌幅'])) if row['涨跌幅'] != '--' else Decimal('0'),
                        'change_percent': float(row['涨跌幅'].replace('%', '')) if row['涨跌幅'] != '--' else 0,
                        'volume': int(row['成交量'].replace('万', '')) * 10000 if isinstance(row['成交量'], str) else row['成交量'],
                        'amount': Decimal(str(row['成交额'].replace('亿', ''))) * 100000000 if isinstance(row['成交额'], str) else row['成交额'],
                        'open_today': Decimal(str(row['今开'])) if row['今开'] != '--' else Decimal('0'),
                        'high': Decimal(str(row['最高'])) if row['最高'] != '--' else Decimal('0'),
                        'low': Decimal(str(row['最低'])) if row['最低'] != '--' else Decimal('0'),
                        'close_yesterday': Decimal(str(row['昨收'])) if row['昨收'] != '--' else Decimal('0'),
                    }
                )
            except Stock.DoesNotExist:
                continue
            except Exception as e:
                print(f"处理 {code} 失败: {e}")
                continue
        
        print(f"实时行情更新完成")
        return True
        
    except Exception as e:
        print(f"获取实时行情失败: {e}")
        return False


if __name__ == '__main__':
    # 示例用法
    # 1. 获取股票列表
    # get_stock_list()
    
    # 2. 获取日线数据
    # get_daily_data('000001')
    
    # 3. 获取实时行情
    # get_realtime_quote('000001')
    
    print("数据采集脚本使用方法:")
    print("  python scripts/data_collector.py get_stock_list")
    print("  python scripts/data_collector.py get_daily_data 000001")
    print("  python scripts/data_collector.py get_realtime_quote 000001")
