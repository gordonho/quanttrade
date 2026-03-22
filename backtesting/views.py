from rest_framework import viewsets
from .models import Backtest, BacktestTrade, BacktestEquity
from .serializers import (
    BacktestSerializer,
    BacktestTradeSerializer,
    BacktestEquitySerializer,
)


class BacktestViewSet(viewsets.ModelViewSet):
    queryset = Backtest.objects.all()
    serializer_class = BacktestSerializer


class BacktestTradeViewSet(viewsets.ModelViewSet):
    queryset = BacktestTrade.objects.all()
    serializer_class = BacktestTradeSerializer


class BacktestEquityViewSet(viewsets.ModelViewSet):
    queryset = BacktestEquity.objects.all()
    serializer_class = BacktestEquitySerializer
