from django.template.loader import render_to_string
from liveview.connections import send
from liveview.decorators import liveview_handler

from web.models import Board, Card, List


def get_board_detail_context(
    board_id,
    editing_board_name=False,
    editing_list_id=None,
    editing_card_id=None,
    adding_card_to_list_id=None,
    show_add_list_form=False,
):
    try:
        board = Board.objects.prefetch_related("lists__cards").get(id=board_id)
        return {
            "title": f"{board.name} | Trello風TODOアプリ",
            "board": board,
            "editing_board_name": editing_board_name,
            "editing_list_id": editing_list_id,
            "editing_card_id": editing_card_id,
            "adding_card_to_list_id": adding_card_to_list_id,
            "show_add_list_form": show_add_list_form,
        }
    except Board.DoesNotExist:
        return None


def render_board_detail_html(board_id, **kwargs):
    context = get_board_detail_context(board_id, **kwargs)
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


@liveview_handler("board_detail->show_edit_board_name")
def show_edit_board_name(consumer, content):
    payload = content.get("data", {})
    board_id = payload.get("board_id")
    if board_id:
        html = render_board_detail_html(board_id, editing_board_name=True)
        if html:
            send(consumer, {"selector": "#main", "html": html})


@liveview_handler("board_detail->update_board_name")
def update_board_name(consumer, content):
    payload = content.get("data", {})
    form_data = content.get("form", {})
    board_id = payload.get("board_id")
    name = form_data.get("name", "").strip()
    if board_id and name:
        try:
            board = Board.objects.get(id=board_id)
            board.name = name
            board.save()
            broadcast_board_update(consumer, board_id)
        except Board.DoesNotExist:
            pass


@liveview_handler("board_detail->show_add_list_form")
def show_add_list_form(consumer, content):
    payload = content.get("data", {})
    board_id = payload.get("board_id")
    if board_id:
        html = render_board_detail_html(board_id, show_add_list_form=True)
        if html:
            send(consumer, {"selector": "#main", "html": html})


@liveview_handler("board_detail->add_list")
def add_list(consumer, content):
    payload = content.get("data", {})
    form_data = content.get("form", {})
    board_id = payload.get("board_id")
    name = form_data.get("name", "").strip()
    if board_id and name:
        try:
            board = Board.objects.get(id=board_id)
            max_position = List.objects.filter(board=board).count()
            List.objects.create(board=board, name=name, position=max_position)
            broadcast_board_update(consumer, board_id)
        except Board.DoesNotExist:
            pass


@liveview_handler("board_detail->show_edit_list")
def show_edit_list(consumer, content):
    payload = content.get("data", {})
    board_id = payload.get("board_id")
    list_id = payload.get("list_id")
    if board_id and list_id:
        try:
            list_id = int(list_id)
        except (ValueError, TypeError):
            list_id = None
        html = render_board_detail_html(board_id, editing_list_id=list_id)
        if html:
            send(consumer, {"selector": "#main", "html": html})


@liveview_handler("board_detail->edit_list")
def edit_list(consumer, content):
    payload = content.get("data", {})
    form_data = content.get("form", {})
    list_id = payload.get("list_id")
    name = form_data.get("name", "").strip()
    board_id = payload.get("board_id")
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
    payload = content.get("data", {})
    list_id = payload.get("list_id")
    board_id = payload.get("board_id")
    if list_id:
        try:
            list_obj = List.objects.get(id=list_id)
            board_id = board_id or list_obj.board_id
            list_obj.delete()
            broadcast_board_update(consumer, board_id)
        except List.DoesNotExist:
            pass


@liveview_handler("board_detail->move_list_left")
def move_list_left(consumer, content):
    payload = content.get("data", {})
    list_id = payload.get("list_id")
    board_id = payload.get("board_id")
    if list_id:
        try:
            list_obj = List.objects.get(id=list_id)
            board_id = board_id or list_obj.board_id
            if list_obj.position > 0:
                lists = list(List.objects.filter(board_id=board_id).order_by("position"))
                current_idx = lists.index(list_obj)
                if current_idx > 0:
                    lists[current_idx], lists[current_idx - 1] = lists[current_idx - 1], lists[current_idx]
                    for i, lst in enumerate(lists):
                        lst.position = i
                        lst.save()
            broadcast_board_update(consumer, board_id)
        except List.DoesNotExist:
            pass


@liveview_handler("board_detail->move_list_right")
def move_list_right(consumer, content):
    payload = content.get("data", {})
    list_id = payload.get("list_id")
    board_id = payload.get("board_id")
    if list_id:
        try:
            list_obj = List.objects.get(id=list_id)
            board_id = board_id or list_obj.board_id
            lists = list(List.objects.filter(board_id=board_id).order_by("position"))
            current_idx = lists.index(list_obj)
            if current_idx < len(lists) - 1:
                lists[current_idx], lists[current_idx + 1] = lists[current_idx + 1], lists[current_idx]
                for i, lst in enumerate(lists):
                    lst.position = i
                    lst.save()
            broadcast_board_update(consumer, board_id)
        except List.DoesNotExist:
            pass


@liveview_handler("board_detail->show_add_card_form")
def show_add_card_form(consumer, content):
    payload = content.get("data", {})
    board_id = payload.get("board_id")
    list_id = payload.get("list_id")
    if board_id and list_id:
        try:
            list_id = int(list_id)
        except (ValueError, TypeError):
            list_id = None
        html = render_board_detail_html(board_id, adding_card_to_list_id=list_id)
        if html:
            send(consumer, {"selector": "#main", "html": html})


@liveview_handler("board_detail->add_card")
def add_card(consumer, content):
    payload = content.get("data", {})
    form_data = content.get("form", {})
    list_id = payload.get("list_id")
    title = form_data.get("title", "").strip()
    board_id = payload.get("board_id")
    if list_id and title:
        try:
            list_obj = List.objects.get(id=list_id)
            max_position = Card.objects.filter(list=list_obj).count()
            Card.objects.create(list=list_obj, title=title, position=max_position)
            broadcast_board_update(consumer, board_id or list_obj.board_id)
        except List.DoesNotExist:
            pass


@liveview_handler("board_detail->show_edit_card")
def show_edit_card(consumer, content):
    payload = content.get("data", {})
    board_id = payload.get("board_id")
    card_id = payload.get("card_id")
    if board_id and card_id:
        try:
            card_id = int(card_id)
        except (ValueError, TypeError):
            card_id = None
        html = render_board_detail_html(board_id, editing_card_id=card_id)
        if html:
            send(consumer, {"selector": "#main", "html": html})


@liveview_handler("board_detail->edit_card")
def edit_card(consumer, content):
    payload = content.get("data", {})
    form_data = content.get("form", {})
    card_id = payload.get("card_id")
    title = form_data.get("title", "").strip()
    board_id = payload.get("board_id")
    if card_id and title:
        try:
            card = Card.objects.get(id=card_id)
            card.title = title
            card.save()
            broadcast_board_update(consumer, board_id or card.list.board_id)
        except Card.DoesNotExist:
            pass


@liveview_handler("board_detail->remove_card")
def remove_card(consumer, content):
    payload = content.get("data", {})
    card_id = payload.get("card_id")
    board_id = payload.get("board_id")
    if card_id:
        try:
            card = Card.objects.get(id=card_id)
            board_id = board_id or card.list.board_id
            card.delete()
            broadcast_board_update(consumer, board_id)
        except Card.DoesNotExist:
            pass


@liveview_handler("board_detail->move_card_up")
def move_card_up(consumer, content):
    payload = content.get("data", {})
    card_id = payload.get("card_id")
    list_id = payload.get("list_id")
    board_id = payload.get("board_id")
    if card_id and list_id:
        try:
            card = Card.objects.get(id=card_id)
            board_id = board_id or card.list.board_id
            cards = list(Card.objects.filter(list_id=list_id).order_by("position"))
            current_idx = cards.index(card)
            if current_idx > 0:
                cards[current_idx], cards[current_idx - 1] = cards[current_idx - 1], cards[current_idx]
                for i, c in enumerate(cards):
                    c.position = i
                    c.save()
            broadcast_board_update(consumer, board_id)
        except Card.DoesNotExist:
            pass


@liveview_handler("board_detail->move_card_down")
def move_card_down(consumer, content):
    payload = content.get("data", {})
    card_id = payload.get("card_id")
    list_id = payload.get("list_id")
    board_id = payload.get("board_id")
    if card_id and list_id:
        try:
            card = Card.objects.get(id=card_id)
            board_id = board_id or card.list.board_id
            cards = list(Card.objects.filter(list_id=list_id).order_by("position"))
            current_idx = cards.index(card)
            if current_idx < len(cards) - 1:
                cards[current_idx], cards[current_idx + 1] = cards[current_idx + 1], cards[current_idx]
                for i, c in enumerate(cards):
                    c.position = i
                    c.save()
            broadcast_board_update(consumer, board_id)
        except Card.DoesNotExist:
            pass
