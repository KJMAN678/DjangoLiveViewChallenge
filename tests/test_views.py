import pytest
from django.test import Client
from django.urls import reverse

from web.models import Board, Card, List


@pytest.mark.django_db
class TestIndexView:
    def test_index_view_status_code(self, client: Client):
        response = client.get("/")
        assert response.status_code == 200

    def test_index_view_template(self, client: Client):
        response = client.get("/")
        assert "web/index.html" in [t.name for t in response.templates]

    def test_index_view_contains_boards(self, client: Client):
        Board.objects.create(name="テストボード1")
        Board.objects.create(name="テストボード2")
        response = client.get("/")
        assert "テストボード1" in response.content.decode()
        assert "テストボード2" in response.content.decode()

    def test_index_view_empty_boards(self, client: Client):
        response = client.get("/")
        assert "ボードがありません" in response.content.decode()


@pytest.mark.django_db
class TestBoardDetailView:
    def test_board_detail_view_status_code(self, client: Client):
        board = Board.objects.create(name="テストボード")
        response = client.get(f"/board/{board.id}/")
        assert response.status_code == 200

    def test_board_detail_view_template(self, client: Client):
        board = Board.objects.create(name="テストボード")
        response = client.get(f"/board/{board.id}/")
        assert "web/board_detail.html" in [t.name for t in response.templates]

    def test_board_detail_view_contains_board_name(self, client: Client):
        board = Board.objects.create(name="テストボード")
        response = client.get(f"/board/{board.id}/")
        assert "テストボード" in response.content.decode()

    def test_board_detail_view_contains_lists(self, client: Client):
        board = Board.objects.create(name="テストボード")
        List.objects.create(board=board, name="リスト1", position=0)
        List.objects.create(board=board, name="リスト2", position=1)
        response = client.get(f"/board/{board.id}/")
        content = response.content.decode()
        assert "リスト1" in content
        assert "リスト2" in content

    def test_board_detail_view_contains_cards(self, client: Client):
        board = Board.objects.create(name="テストボード")
        list_obj = List.objects.create(board=board, name="リスト1", position=0)
        Card.objects.create(list=list_obj, title="カード1", position=0)
        Card.objects.create(list=list_obj, title="カード2", position=1)
        response = client.get(f"/board/{board.id}/")
        content = response.content.decode()
        assert "カード1" in content
        assert "カード2" in content

    def test_board_detail_view_nonexistent_board(self, client: Client):
        response = client.get("/board/99999/")
        assert response.status_code == 200
        assert "ボードが見つかりません" in response.content.decode()
