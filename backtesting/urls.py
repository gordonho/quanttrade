from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BacktestViewSet, BacktestTradeViewSet, BacktestEquityViewSet

router = DefaultRouter()
router.register(r"backtests", BacktestViewSet)
router.register(r"trades", BacktestTradeViewSet)
router.register(r"equity", BacktestEquityViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
