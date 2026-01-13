"""
ビューモジュール

Trello風TODOアプリのビュークラスを定義します。
"""

from django.views.generic import TemplateView

from web.models import Board


class IndexView(TemplateView):
    """
    ボード一覧ページのビュークラス。

    トップページとして、すべてのボードを一覧表示します。
    """

    template_name = "web/index.html"

    def get_context_data(self, **kwargs):
        """
        テンプレートに渡すコンテキストデータを取得する。

        Returns:
            dict: ボード一覧とページタイトルを含むコンテキスト辞書
        """
        context = super().get_context_data(**kwargs)
        context["boards"] = Board.objects.all()
        context["title"] = "ボード一覧 | Trello風TODOアプリ"
        return context


class BoardDetailView(TemplateView):
    """
    ボード詳細ページのビュークラス。

    指定されたボードの詳細情報（リストとカードを含む）を表示します。
    """

    template_name = "web/board_detail.html"

    def get_context_data(self, **kwargs):
        """
        テンプレートに渡すコンテキストデータを取得する。

        URLパラメータからボードIDを取得し、該当するボードの情報を
        リストとカードを含めてプリフェッチして返します。

        Returns:
            dict: ボード情報とページタイトルを含むコンテキスト辞書
        """
        context = super().get_context_data(**kwargs)
        board_id = self.kwargs.get("board_id")
        try:
            board = Board.objects.prefetch_related("lists__cards").get(id=board_id)
            context["board"] = board
            context["title"] = f"{board.name} | Trello風TODOアプリ"
        except Board.DoesNotExist:
            context["board"] = None
            context["title"] = "ボードが見つかりません"
        return context
