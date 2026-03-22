from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import StrategyViewSet, StrategySignalViewSet, StrategyParameterViewSet

router = DefaultRouter()
router.register(r'strategies', StrategyViewSet)
router.register(r'signals', StrategySignalViewSet)
router.register(r'parameters', StrategyParameterViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
