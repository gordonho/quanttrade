from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OrderViewSet, TradeViewSet, PositionViewSet

router = DefaultRouter()
router.register(r"orders", OrderViewSet)
router.register(r"trades", TradeViewSet)
router.register(r"positions", PositionViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
