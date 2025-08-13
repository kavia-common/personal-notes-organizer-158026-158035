from typing import Optional

from django.contrib.auth import get_user_model
from django.db.models import Q, QuerySet
from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import api_view
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Category, Note, Tag
from .serializers import (
    CategorySerializer,
    NoteSerializer,
    RegisterSerializer,
    TagSerializer,
    UserSerializer,
)

User = get_user_model()


# PUBLIC_INTERFACE
@api_view(["GET"])
def health(request: Request) -> Response:
    # PUBLIC_INTERFACE
    """Health check endpoint.

    Returns:
        200 OK with a simple payload to indicate server is healthy.
    """
    return Response({"message": "Server is up!"})


class IsOwner(permissions.BasePermission):
    """Permission that allows access only to the object's owner."""

    # PUBLIC_INTERFACE
    def has_object_permission(self, request: Request, view, obj) -> bool:
        """Grant if object has 'user' and matches the requesting user."""
        return hasattr(obj, "user") and getattr(obj, "user") == request.user


class BaseOwnedViewSet(viewsets.ModelViewSet):
    """Base viewset filtering queryset to the authenticated user."""
    permission_classes = [IsAuthenticated, IsOwner]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields: list[str] = []
    ordering_fields: list[str] = ["created_at", "updated_at", "id"]
    ordering = ["-updated_at"]

    queryset = None  # type: ignore

    # PUBLIC_INTERFACE
    def get_queryset(self) -> QuerySet:
        """Limit queryset to request.user; overridden in subclasses."""
        raise NotImplementedError("Subclasses must implement get_queryset()")


class TagViewSet(BaseOwnedViewSet):
    """Tags CRUD. Names are unique per user."""
    serializer_class = TagSerializer
    queryset = Tag.objects.none()
    search_fields = ["name"]
    ordering_fields = ["name", "created_at", "updated_at"]

    # PUBLIC_INTERFACE
    @swagger_auto_schema(operation_summary="List tags", operation_description="List all tags for the authenticated user.")
    def list(self, request: Request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    # PUBLIC_INTERFACE
    def get_queryset(self) -> QuerySet:
        """Return tags owned by the authenticated user."""
        return Tag.objects.filter(user=self.request.user)

    # PUBLIC_INTERFACE
    @swagger_auto_schema(operation_summary="Create tag", operation_description="Create a new tag for the authenticated user.")
    def create(self, request: Request, *args, **kwargs):
        return super().create(request, *args, **kwargs)


class CategoryViewSet(BaseOwnedViewSet):
    """Categories CRUD. Names are unique per user."""
    serializer_class = CategorySerializer
    queryset = Category.objects.none()
    search_fields = ["name"]
    ordering_fields = ["name", "created_at", "updated_at"]

    # PUBLIC_INTERFACE
    def get_queryset(self) -> QuerySet:
        """Return categories owned by the authenticated user."""
        return Category.objects.filter(user=self.request.user)


class NoteViewSet(BaseOwnedViewSet):
    """Notes CRUD with filtering by tag, category, archived state, and search."""
    serializer_class = NoteSerializer
    queryset = Note.objects.none()
    search_fields = ["title", "content"]
    ordering_fields = ["title", "created_at", "updated_at"]

    # PUBLIC_INTERFACE
    def get_queryset(self) -> QuerySet:
        """Return notes owned by the authenticated user with optional filters.

        Query parameters:
        - q: search text contained in title or content
        - tag: filter by tag id (int) or name (str)
        - category: filter by category id (int)
        - archived: true/false to filter archived state
        """
        qs = Note.objects.filter(user=self.request.user)

        q: Optional[str] = self.request.query_params.get("q")
        tag_param: Optional[str] = self.request.query_params.get("tag")
        category_param: Optional[str] = self.request.query_params.get("category")
        archived_param: Optional[str] = self.request.query_params.get("archived")

        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(content__icontains=q))

        if tag_param:
            if tag_param.isdigit():
                qs = qs.filter(tags__id=int(tag_param))
            else:
                qs = qs.filter(tags__name__iexact=tag_param)

        if category_param and category_param.isdigit():
            qs = qs.filter(category__id=int(category_param))

        if archived_param is not None:
            if archived_param.lower() in {"true", "1", "yes"}:
                qs = qs.filter(is_archived=True)
            elif archived_param.lower() in {"false", "0", "no"}:
                qs = qs.filter(is_archived=False)

        return qs.distinct()

    # PUBLIC_INTERFACE
    @swagger_auto_schema(operation_summary="Create note", operation_description="Create a new note. Tags and category must belong to the user.")
    def create(self, request: Request, *args, **kwargs):
        return super().create(request, *args, **kwargs)


class RegisterAPIView(APIView):
    """Register a new user account."""
    permission_classes = [permissions.AllowAny]

    # PUBLIC_INTERFACE
    @swagger_auto_schema(
        operation_id="auth_register",
        operation_summary="Register",
        operation_description="Create a new user account with username, email, and password.",
        request_body=RegisterSerializer,
        responses={201: UserSerializer()},
        tags=["auth"],
    )
    def post(self, request: Request, *args, **kwargs) -> Response:
        """Register a new user.

        Body:
        - username: string
        - email: string
        - password: string (min 8 chars)

        Returns:
            201 created with user profile (id, username, email).
        """
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class MeAPIView(APIView):
    """Return current authenticated user profile."""
    permission_classes = [IsAuthenticated]

    # PUBLIC_INTERFACE
    @swagger_auto_schema(
        operation_id="auth_me",
        operation_summary="Current user",
        operation_description="Get the profile for the authenticated user.",
        responses={200: UserSerializer()},
        tags=["auth"],
    )
    def get(self, request: Request, *args, **kwargs) -> Response:
        """Return the current authenticated user's basic profile info."""
        return Response(UserSerializer(request.user).data, status=status.HTTP_200_OK)
