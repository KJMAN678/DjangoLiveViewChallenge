from django.template.loader import render_to_string
from liveview.connections import send
from liveview.decorators import liveview_handler

from web.models import Board


def get_boards_context():
    return {
        "title": "ボード一覧 | Trello風TODOアプリ",
        "boards": list(Board.objects.all()),
    }


def render_boards_html():
    context = get_boards_context()
    return render_to_string("web/pages/boards.html", context)


def broadcast_boards_update(consumer):
    html = render_boards_html()
    data = {
        "selector": "#main",
        "html": html,
    }
    consumer.broadcast_to_all(data)


@liveview_handler("boards->send_page")
def send_page(consumer, content):
    context = get_boards_context()
    html = render_to_string("web/pages/boards.html", context)
    data = {
        "selector": "#main",
        "html": html,
        "url": "/",
        "title": context["title"],
    }
    send(consumer, data)


@liveview_handler("boards->create")
def create(consumer, content):
    data = content.get("data", {})
    name = data.get("name", "").strip()
    if name:
        Board.objects.create(name=name)
        broadcast_boards_update(consumer)
    else:
        html = render_boards_html()
        data = {
            "selector": "#main",
            "html": html,
        }
        send(consumer, data)


@liveview_handler("boards->update")
def update(consumer, content):
    data = content.get("data", {})
    board_id = data.get("board_id")
    name = data.get("name", "").strip()
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
        data = {
            "selector": "#main",
            "html": html,
        }
        send(consumer, data)


@liveview_handler("boards->delete")
def delete(consumer, content):
    data = content.get("data", {})
    board_id = data.get("board_id")
    if board_id:
        try:
            board = Board.objects.get(id=board_id)
            board.delete()
            broadcast_boards_update(consumer)
        except Board.DoesNotExist:
            pass
    else:
        html = render_boards_html()
        data = {
            "selector": "#main",
            "html": html,
        }
        send(consumer, data)
