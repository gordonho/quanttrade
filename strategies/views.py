from rest_framework import viewsets
from .models import Strategy, StrategySignal, StrategyParameter
from .serializers import (
    StrategySerializer,
    StrategySignalSerializer,
    StrategyParameterSerializer,
)


class StrategyViewSet(viewsets.ModelViewSet):
    queryset = Strategy.objects.all()
    serializer_class = StrategySerializer


class StrategySignalViewSet(viewsets.ModelViewSet):
    queryset = StrategySignal.objects.all()
    serializer_class = StrategySignalSerializer


class StrategyParameterViewSet(viewsets.ModelViewSet):
    queryset = StrategyParameter.objects.all()
    serializer_class = StrategyParameterSerializer
