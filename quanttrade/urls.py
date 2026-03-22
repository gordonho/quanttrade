"""
URL configuration for quanttrade project.
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API routes
    path('api/users/', include('users.urls')),
    path('api/market/', include('market_data.urls')),
    path('api/strategies/', include('strategies.urls')),
    path('api/backtesting/', include('backtesting.urls')),
    path('api/trading/', include('trading.urls')),
    path('api/portfolio/', include('portfolio.urls')),
    
    # JWT Token
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
