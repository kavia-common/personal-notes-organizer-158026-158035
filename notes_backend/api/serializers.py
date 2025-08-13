from typing import Any

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db import IntegrityError, transaction
from rest_framework import serializers

from .models import Category, Note, Tag

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for authenticated user profile data."""

    class Meta:
        model = User
        fields = ["id", "username", "email"]


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer to register a new user account."""
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["username", "email", "password"]

    def validate_password(self, value: str) -> str:
        validate_password(value)
        return value

    # PUBLIC_INTERFACE
    def create(self, validated_data: dict) -> User:
        """Create a new user with a hashed password."""
        try:
            with transaction.atomic():
                user = User.objects.create_user(
                    username=validated_data["username"],
                    email=validated_data.get("email"),
                    password=validated_data["password"],
                )
            return user
        except IntegrityError as e:
            raise serializers.ValidationError({"username": "Username already exists"}) from e


class TagSerializer(serializers.ModelSerializer):
    """Serializer for tag resources."""

    class Meta:
        model = Tag
        fields = ["id", "name", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

    # PUBLIC_INTERFACE
    def create(self, validated_data: dict) -> Tag:
        """Create tag for the requesting user."""
        request = self.context.get("request")
        return Tag.objects.create(user=request.user, **validated_data)


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for category resources."""

    class Meta:
        model = Category
        fields = ["id", "name", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

    # PUBLIC_INTERFACE
    def create(self, validated_data: dict) -> Category:
        """Create category for the requesting user."""
        request = self.context.get("request")
        return Category.objects.create(user=request.user, **validated_data)


class NoteSerializer(serializers.ModelSerializer):
    """Serializer for note resources with tag and category relations."""
    tags = serializers.PrimaryKeyRelatedField(
        many=True, required=False, queryset=Tag.objects.none()
    )
    category = serializers.PrimaryKeyRelatedField(
        required=False, allow_null=True, queryset=Category.objects.none()
    )

    class Meta:
        model = Note
        fields = [
            "id",
            "title",
            "content",
            "is_archived",
            "category",
            "tags",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def _limit_querysets_to_user(self):
        request = self.context.get("request")
        if request and request.user and request.user.is_authenticated:
            self.fields["tags"].queryset = Tag.objects.filter(user=request.user)
            self.fields["category"].queryset = Category.objects.filter(user=request.user)

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._limit_querysets_to_user()

    # PUBLIC_INTERFACE
    def create(self, validated_data: dict) -> Note:
        """Create note for the requesting user."""
        request = self.context.get("request")
        tag_list = validated_data.pop("tags", [])
        note = Note.objects.create(user=request.user, **validated_data)
        if tag_list:
            note.tags.set(tag_list)
        return note

    # PUBLIC_INTERFACE
    def update(self, instance: Note, validated_data: dict) -> Note:
        """Update note fields including tags and category."""
        tag_list = validated_data.pop("tags", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if tag_list is not None:
            instance.tags.set(tag_list)
        return instance
