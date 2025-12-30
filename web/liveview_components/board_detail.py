from django.template.loader import render_to_string
from liveview.connections import send
from liveview.decorators import liveview_handler

from web.models import Board, Card, List


def get_board_detail_context(board_id):
    try:
        board = Board.objects.prefetch_related("lists__cards").get(id=board_id)
        return {
            "title": f"{board.name} | Trello風TODOアプリ",
            "board": board,
        }
    except Board.DoesNotExist:
        return None


def render_board_detail_html(board_id):
    context = get_board_detail_context(board_id)
    if context:
        return render_to_string("web/pages/board_detail.html", context)
    return None


def broadcast_board_update(consumer, board_id):
    html = render_board_detail_html(board_id)
    if html:
        data = {
            "selector": "#main",
            "html": html,
        }
        consumer.broadcast_to_all(data)


@liveview_handler("board_detail->send_page")
def send_page(consumer, content):
    data = content.get("data", {})
    board_id = data.get("board_id")
    if board_id:
        context = get_board_detail_context(board_id)
        if context:
            html = render_to_string("web/pages/board_detail.html", context)
            response_data = {
                "selector": "#main",
                "html": html,
                "url": f"/board/{board_id}/",
                "title": context["title"],
            }
            send(consumer, response_data)


@liveview_handler("board_detail->update_board_name")
def update_board_name(consumer, content):
    data = content.get("data", {})
    board_id = data.get("board_id")
    name = data.get("name", "").strip()
    if board_id and name:
        try:
            board = Board.objects.get(id=board_id)
            board.name = name
            board.save()
            broadcast_board_update(consumer, board_id)
        except Board.DoesNotExist:
            pass


@liveview_handler("board_detail->add_list")
def add_list(consumer, content):
    data = content.get("data", {})
    board_id = data.get("board_id")
    name = data.get("name", "").strip()
    if board_id and name:
        try:
            board = Board.objects.get(id=board_id)
            max_position = List.objects.filter(board=board).count()
            List.objects.create(board=board, name=name, position=max_position)
            broadcast_board_update(consumer, board_id)
        except Board.DoesNotExist:
            pass


@liveview_handler("board_detail->edit_list")
def edit_list(consumer, content):
    data = content.get("data", {})
    list_id = data.get("list_id")
    name = data.get("name", "").strip()
    board_id = data.get("board_id")
    if list_id and name:
        try:
            list_obj = List.objects.get(id=list_id)
            list_obj.name = name
            list_obj.save()
            broadcast_board_update(consumer, board_id or list_obj.board_id)
        except List.DoesNotExist:
            pass


@liveview_handler("board_detail->remove_list")
def remove_list(consumer, content):
    data = content.get("data", {})
    list_id = data.get("list_id")
    board_id = data.get("board_id")
    if list_id:
        try:
            list_obj = List.objects.get(id=list_id)
            board_id = board_id or list_obj.board_id
            list_obj.delete()
            broadcast_board_update(consumer, board_id)
        except List.DoesNotExist:
            pass


@liveview_handler("board_detail->add_card")
def add_card(consumer, content):
    data = content.get("data", {})
    list_id = data.get("list_id")
    title = data.get("title", "").strip()
    board_id = data.get("board_id")
    if list_id and title:
        try:
            list_obj = List.objects.get(id=list_id)
            max_position = Card.objects.filter(list=list_obj).count()
            Card.objects.create(list=list_obj, title=title, position=max_position)
            broadcast_board_update(consumer, board_id or list_obj.board_id)
        except List.DoesNotExist:
            pass


@liveview_handler("board_detail->edit_card")
def edit_card(consumer, content):
    data = content.get("data", {})
    card_id = data.get("card_id")
    title = data.get("title", "").strip()
    description = data.get("description", "")
    board_id = data.get("board_id")
    if card_id and title:
        try:
            card = Card.objects.get(id=card_id)
            card.title = title
            card.description = description
            card.save()
            broadcast_board_update(consumer, board_id or card.list.board_id)
        except Card.DoesNotExist:
            pass


@liveview_handler("board_detail->remove_card")
def remove_card(consumer, content):
    data = content.get("data", {})
    card_id = data.get("card_id")
    board_id = data.get("board_id")
    if card_id:
        try:
            card = Card.objects.get(id=card_id)
            board_id = board_id or card.list.board_id
            card.delete()
            broadcast_board_update(consumer, board_id)
        except Card.DoesNotExist:
            pass


@liveview_handler("board_detail->reorder_list")
def reorder_list(consumer, content):
    data = content.get("data", {})
    list_id = data.get("list_id")
    new_position = data.get("target_position") or data.get("new_position")
    board_id = data.get("board_id")
    if list_id is not None and new_position is not None:
        try:
            list_obj = List.objects.get(id=list_id)
            board_id = board_id or list_obj.board_id
            lists = list(List.objects.filter(board_id=board_id).order_by("position"))
            lists.remove(list_obj)
            lists.insert(int(new_position), list_obj)
            for i, lst in enumerate(lists):
                lst.position = i
                lst.save()
            broadcast_board_update(consumer, board_id)
        except List.DoesNotExist:
            pass


@liveview_handler("board_detail->reorder_card")
def reorder_card(consumer, content):
    data = content.get("data", {})
    card_id = data.get("card_id")
    target_list_id = data.get("target_list_id")
    new_position = data.get("target_position") or data.get("new_position")
    board_id = data.get("board_id")
    if card_id is not None and target_list_id is not None and new_position is not None:
        try:
            card = Card.objects.get(id=card_id)
            target_list = List.objects.get(id=target_list_id)
            board_id = board_id or target_list.board_id
            
            old_list = card.list
            if old_list.id != target_list.id:
                old_cards = list(Card.objects.filter(list=old_list).exclude(id=card_id).order_by("position"))
                for i, c in enumerate(old_cards):
                    c.position = i
                    c.save()
            
            card.list = target_list
            card.save()
            
            target_cards = list(Card.objects.filter(list=target_list).exclude(id=card_id).order_by("position"))
            target_cards.insert(int(new_position), card)
            for i, c in enumerate(target_cards):
                c.position = i
                c.save()
            
            broadcast_board_update(consumer, board_id)
        except (Card.DoesNotExist, List.DoesNotExist):
            pass
