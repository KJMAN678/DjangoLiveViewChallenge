"""
モデルモジュール

Trello風TODOアプリのデータモデルを定義します。
Board（ボード）、List（リスト）、Card（カード）の3層構造で
タスクを管理します。
"""

from django.db import models


class Board(models.Model):
    """
    ボードモデル（Trelloのボードに相当）。

    複数のリストを含むことができる最上位のコンテナです。
    プロジェクトやカテゴリごとにボードを作成して管理します。

    Attributes:
        name: ボードの名前
        created_at: 作成日時（自動設定）
        updated_at: 更新日時（自動更新）
    """

    name = models.CharField(max_length=255, verbose_name="ボード名")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="作成日時")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新日時")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "ボード"
        verbose_name_plural = "ボード"

    def __str__(self) -> str:
        """
        ボードの文字列表現を返す。

        Returns:
            str: ボード名
        """
        return self.name


class List(models.Model):
    """
    リストモデル（Trelloのリスト/カラムに相当）。

    ボード内でカードをグループ化するためのコンテナです。
    「TODO」「進行中」「完了」などのステータスを表現するのに使用します。

    Attributes:
        board: 所属するボード（外部キー）
        name: リストの名前
        position: 表示順序（0から始まる整数）
        created_at: 作成日時（自動設定）
        updated_at: 更新日時（自動更新）
    """

    board = models.ForeignKey(
        Board,
        on_delete=models.CASCADE,
        related_name="lists",
        verbose_name="ボード",
    )
    name = models.CharField(max_length=255, verbose_name="リスト名")
    position = models.PositiveIntegerField(default=0, verbose_name="位置")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="作成日時")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新日時")

    class Meta:
        ordering = ["position"]
        verbose_name = "リスト"
        verbose_name_plural = "リスト"

    def __str__(self) -> str:
        """
        リストの文字列表現を返す。

        Returns:
            str: リスト名
        """
        return self.name


class Card(models.Model):
    """
    カードモデル（Trelloのカード/タスクに相当）。

    個々のタスクや作業項目を表します。
    リスト内で上下に並び替えることができます。

    Attributes:
        list: 所属するリスト（外部キー）
        title: カードのタイトル
        position: 表示順序（0から始まる整数）
        created_at: 作成日時（自動設定）
        updated_at: 更新日時（自動更新）
    """

    list = models.ForeignKey(
        List,
        on_delete=models.CASCADE,
        related_name="cards",
        verbose_name="リスト",
    )
    title = models.CharField(max_length=255, verbose_name="タイトル")
    position = models.PositiveIntegerField(default=0, verbose_name="位置")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="作成日時")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新日時")

    class Meta:
        ordering = ["position"]
        verbose_name = "カード"
        verbose_name_plural = "カード"

    def __str__(self) -> str:
        """
        カードの文字列表現を返す。

        Returns:
            str: カードのタイトル
        """
        return self.title
