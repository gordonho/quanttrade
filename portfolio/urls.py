from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PortfolioViewSet, PortfolioHistoryViewSet, PortfolioAllocationViewSet

router = DefaultRouter()
router.register(r'portfolios', PortfolioViewSet)
router.register(r'portfolio-history', PortfolioHistoryViewSet)
router.register(r'portfolio-allocations', PortfolioAllocationViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
