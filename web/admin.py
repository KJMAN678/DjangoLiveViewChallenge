"""
管理画面モジュール

Django管理画面でBoard、List、Cardモデルを管理するための
AdminクラスとAdmin設定を定義します。
"""

from django.contrib import admin

from web.models import Board, Card, List


@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    """
    ボードモデルの管理画面設定。

    ボード名での検索と、作成日時・更新日時の表示をサポートします。
    """

    list_display = ["name", "created_at", "updated_at"]
    search_fields = ["name"]


@admin.register(List)
class ListAdmin(admin.ModelAdmin):
    """
    リストモデルの管理画面設定。

    ボードでのフィルタリングと、リスト名での検索をサポートします。
    位置情報も一覧に表示されます。
    """

    list_display = ["name", "board", "position", "created_at", "updated_at"]
    list_filter = ["board"]
    search_fields = ["name"]


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    """
    カードモデルの管理画面設定。

    リストおよびボードでのフィルタリングと、タイトルでの検索をサポートします。
    位置情報も一覧に表示されます。
    """

    list_display = ["title", "list", "position", "created_at", "updated_at"]
    list_filter = ["list", "list__board"]
    search_fields = ["title"]
