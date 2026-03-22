from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import StockViewSet, DailyDataViewSet

router = DefaultRouter()
router.register(r'stocks', StockViewSet)
router.register(r'daily-data', DailyDataViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
