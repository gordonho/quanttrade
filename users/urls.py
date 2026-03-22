from rest_framework.routers import DefaultRouter
from .views import UserViewSet, APIKeyViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'apikeys', APIKeyViewSet, basename='apikey')

urlpatterns = router.urls
