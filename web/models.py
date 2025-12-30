from django.db import models


class Board(models.Model):
    """ボード（Trelloのボードに相当）"""

    name = models.CharField(max_length=255, verbose_name="ボード名")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="作成日時")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新日時")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "ボード"
        verbose_name_plural = "ボード"

    def __str__(self) -> str:
        return self.name


class List(models.Model):
    """リスト（Trelloのリスト/カラムに相当）"""

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
        return self.name


class Card(models.Model):
    """カード（Trelloのカード/タスクに相当）"""

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
        return self.title
