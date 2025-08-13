from django.contrib import admin

from .models import Category, Note, Tag


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "user", "created_at")
    search_fields = ("name", "user__username")
    list_filter = ("user",)
    ordering = ("name",)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "user", "created_at")
    search_fields = ("name", "user__username")
    list_filter = ("user",)
    ordering = ("name",)


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "user", "category", "is_archived", "updated_at")
    search_fields = ("title", "content", "user__username")
    list_filter = ("is_archived", "category", "user")
    filter_horizontal = ("tags",)
    ordering = ("-updated_at",)
