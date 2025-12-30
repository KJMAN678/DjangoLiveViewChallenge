from django.contrib import admin

from web.models import Board, Card, List


@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    list_display = ["name", "created_at", "updated_at"]
    search_fields = ["name"]


@admin.register(List)
class ListAdmin(admin.ModelAdmin):
    list_display = ["name", "board", "position", "created_at", "updated_at"]
    list_filter = ["board"]
    search_fields = ["name"]


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = ["title", "list", "position", "created_at", "updated_at"]
    list_filter = ["list", "list__board"]
    search_fields = ["title"]
