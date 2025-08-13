from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import (
    CategoryViewSet,
    MeAPIView,
    NoteViewSet,
    RegisterAPIView,
    TagViewSet,
    health,
)

router = DefaultRouter()
router.register(r"notes", NoteViewSet, basename="notes")
router.register(r"tags", TagViewSet, basename="tags")
router.register(r"categories", CategoryViewSet, basename="categories")

urlpatterns = [
    path("health/", health, name="Health"),
    # Auth
    path("auth/register/", RegisterAPIView.as_view(), name="auth-register"),
    path("auth/me/", MeAPIView.as_view(), name="auth-me"),
    path("auth/token/", TokenObtainPairView.as_view(), name="auth-token"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="auth-token-refresh"),
    # Resources
    path("", include(router.urls)),
]
