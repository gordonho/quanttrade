from rest_framework import viewsets, permissions
from .models import Portfolio, PortfolioHistory, PortfolioAllocation
from .serializers import PortfolioSerializer, PortfolioHistorySerializer, PortfolioAllocationSerializer


class PortfolioViewSet(viewsets.ModelViewSet):
    """投资组合视图集"""
    serializer_class = PortfolioSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Portfolio.objects.all()
    
    def get_queryset(self):
        return Portfolio.objects.filter(user=self.request.user).prefetch_related('allocations', 'history')
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class PortfolioHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """组合历史净值视图集"""
    serializer_class = PortfolioHistorySerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = PortfolioHistory.objects.all()
    
    def get_queryset(self):
        return PortfolioHistory.objects.filter(portfolio__user=self.request.user)


class PortfolioAllocationViewSet(viewsets.ModelViewSet):
    """资产配置视图集"""
    serializer_class = PortfolioAllocationSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = PortfolioAllocation.objects.all()
    
    def get_queryset(self):
        return PortfolioAllocation.objects.filter(portfolio__user=self.request.user)
    
    def perform_create(self, serializer):
        portfolio = serializer.validated_data['portfolio']
        if portfolio.user != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You don't have permission to modify this portfolio")
        serializer.save()
