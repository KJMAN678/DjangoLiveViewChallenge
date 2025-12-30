import pytest

from web.models import Board, Card, List


@pytest.mark.django_db
class TestBoardModel:
    def test_create_board(self):
        board = Board.objects.create(name="テストボード")
        assert board.name == "テストボード"
        assert board.id is not None

    def test_board_str(self):
        board = Board.objects.create(name="テストボード")
        assert str(board) == "テストボード"

    def test_board_ordering(self):
        board1 = Board.objects.create(name="ボード1")
        board2 = Board.objects.create(name="ボード2")
        boards = list(Board.objects.all())
        assert boards[0] == board2
        assert boards[1] == board1


@pytest.mark.django_db
class TestListModel:
    def test_create_list(self):
        board = Board.objects.create(name="テストボード")
        list_obj = List.objects.create(board=board, name="テストリスト", position=0)
        assert list_obj.name == "テストリスト"
        assert list_obj.board == board
        assert list_obj.position == 0

    def test_list_str(self):
        board = Board.objects.create(name="テストボード")
        list_obj = List.objects.create(board=board, name="テストリスト", position=0)
        assert str(list_obj) == "テストリスト"

    def test_list_ordering(self):
        board = Board.objects.create(name="テストボード")
        list1 = List.objects.create(board=board, name="リスト1", position=1)
        list2 = List.objects.create(board=board, name="リスト2", position=0)
        lists = list(board.lists.all())
        assert lists[0] == list2
        assert lists[1] == list1

    def test_list_cascade_delete(self):
        board = Board.objects.create(name="テストボード")
        List.objects.create(board=board, name="テストリスト", position=0)
        assert List.objects.count() == 1
        board.delete()
        assert List.objects.count() == 0


@pytest.mark.django_db
class TestCardModel:
    def test_create_card(self):
        board = Board.objects.create(name="テストボード")
        list_obj = List.objects.create(board=board, name="テストリスト", position=0)
        card = Card.objects.create(list=list_obj, title="テストカード", position=0)
        assert card.title == "テストカード"
        assert card.list == list_obj
        assert card.position == 0

    def test_card_str(self):
        board = Board.objects.create(name="テストボード")
        list_obj = List.objects.create(board=board, name="テストリスト", position=0)
        card = Card.objects.create(list=list_obj, title="テストカード", position=0)
        assert str(card) == "テストカード"

    def test_card_ordering(self):
        board = Board.objects.create(name="テストボード")
        list_obj = List.objects.create(board=board, name="テストリスト", position=0)
        card1 = Card.objects.create(list=list_obj, title="カード1", position=1)
        card2 = Card.objects.create(list=list_obj, title="カード2", position=0)
        cards = list(list_obj.cards.all())
        assert cards[0] == card2
        assert cards[1] == card1

    def test_card_cascade_delete(self):
        board = Board.objects.create(name="テストボード")
        list_obj = List.objects.create(board=board, name="テストリスト", position=0)
        Card.objects.create(list=list_obj, title="テストカード", position=0)
        assert Card.objects.count() == 1
        list_obj.delete()
        assert Card.objects.count() == 0
