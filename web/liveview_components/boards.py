from django.template.loader import render_to_string
from liveview.connections import send
from liveview.decorators import liveview_handler

from web.models import Board


def get_boards_context(show_new_board_form=False, editing_board_id=None):
    return {
        "title": "ボード一覧 | Trello風TODOアプリ",
        "boards": list(Board.objects.all()),
        "show_new_board_form": show_new_board_form,
        "editing_board_id": editing_board_id,
    }


def render_boards_html(show_new_board_form=False, editing_board_id=None):
    context = get_boards_context(show_new_board_form, editing_board_id)
    return render_to_string("web/pages/boards.html", context)


def broadcast_boards_update(consumer):
    html = render_boards_html()
    data = {
        "target": "#main",
        "html": html,
    }
    consumer.broadcast_to_all(data)


@liveview_handler("boards->send_page")
def send_page(consumer, content):
    context = get_boards_context()
    html = render_to_string("web/pages/boards.html", context)
    data = {
        "target": "#main",
        "html": html,
        "url": "/",
        "title": context["title"],
    }
    send(consumer, data)


@liveview_handler("boards->show_new_form")
def show_new_form(consumer, content):
    context = get_boards_context(show_new_board_form=True)
    html = render_to_string("web/pages/boards.html", context)
    data = {
        "target": "#main",
        "html": html,
    }
    send(consumer, data)


@liveview_handler("boards->show_edit")
def show_edit(consumer, content):
    payload = content.get("data", {})
    board_id = payload.get("board_id")
    if board_id:
        try:
            board_id = int(board_id)
        except (ValueError, TypeError):
            board_id = None
    context = get_boards_context(editing_board_id=board_id)
    html = render_to_string("web/pages/boards.html", context)
    data = {
        "target": "#main",
        "html": html,
    }
    send(consumer, data)


@liveview_handler("boards->create")
def create(consumer, content):
    form_data = content.get("form", {})
    name = form_data.get("name", "").strip()
    if name:
        Board.objects.create(name=name)
        broadcast_boards_update(consumer)
    else:
        html = render_boards_html()
        response_data = {
            "target": "#main",
            "html": html,
        }
        send(consumer, response_data)


@liveview_handler("boards->update")
def update(consumer, content):
    payload = content.get("data", {})
    form_data = content.get("form", {})
    board_id = payload.get("board_id")
    name = form_data.get("name", "").strip()
    if board_id and name:
        try:
            board = Board.objects.get(id=board_id)
            board.name = name
            board.save()
            broadcast_boards_update(consumer)
        except Board.DoesNotExist:
            pass
    else:
        html = render_boards_html()
        response_data = {
            "target": "#main",
            "html": html,
        }
        send(consumer, response_data)


@liveview_handler("boards->delete")
def delete(consumer, content):
    payload = content.get("data", {})
    board_id = payload.get("board_id")
    if board_id:
        try:
            board = Board.objects.get(id=board_id)
            board.delete()
            broadcast_boards_update(consumer)
        except Board.DoesNotExist:
            pass
    else:
        html = render_boards_html()
        response_data = {
            "target": "#main",
            "html": html,
        }
        send(consumer, response_data)
