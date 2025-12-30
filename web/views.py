from django.views.generic import TemplateView

from web.models import Board


class IndexView(TemplateView):
    template_name = "web/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["boards"] = Board.objects.all()
        context["title"] = "ボード一覧 | Trello風TODOアプリ"
        return context


class BoardDetailView(TemplateView):
    template_name = "web/board_detail.html"

    def get_context_data(self, **kwargs):
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
