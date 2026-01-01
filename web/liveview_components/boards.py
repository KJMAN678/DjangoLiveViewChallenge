"""
ボード一覧ページのLiveViewハンドラモジュール

ボード一覧ページでのCRUD操作を処理するWebSocketハンドラを定義します。
Django-LiveViewのliveview_handlerデコレータを使用して、
クライアントからのアクションに応答します。
"""

from django.template.loader import render_to_string
from liveview.connections import send
from liveview.decorators import liveview_handler

from web.models import Board


def get_boards_context(show_new_board_form=False, editing_board_id=None):
    """
    ボード一覧ページのコンテキストデータを取得する。

    Args:
        show_new_board_form: 新規ボード作成フォームを表示するかどうか
        editing_board_id: 編集中のボードID（編集フォームを表示する場合）

    Returns:
        dict: テンプレートに渡すコンテキスト辞書
    """
    return {
        "title": "ボード一覧 | Trello風TODOアプリ",
        "boards": list(Board.objects.all()),
        "show_new_board_form": show_new_board_form,
        "editing_board_id": editing_board_id,
    }


def render_boards_html(show_new_board_form=False, editing_board_id=None):
    """
    ボード一覧ページのHTMLをレンダリングする。

    Args:
        show_new_board_form: 新規ボード作成フォームを表示するかどうか
        editing_board_id: 編集中のボードID

    Returns:
        str: レンダリングされたHTML文字列
    """
    context = get_boards_context(show_new_board_form, editing_board_id)
    return render_to_string("web/pages/boards.html", context)


def broadcast_boards_update(consumer):
    """
    全クライアントにボード一覧の更新をブロードキャストする。

    同じWebSocketルームに接続している全クライアントに
    最新のボード一覧HTMLを送信します。

    Args:
        consumer: WebSocketコンシューマーインスタンス
    """
    html = render_boards_html()
    data = {
        "target": "#main",
        "html": html,
    }
    consumer.broadcast_to_all(data)


@liveview_handler("boards->send_page")
def send_page(consumer, content):
    """
    ボード一覧ページを送信する。

    SPA遷移時にボード一覧ページのHTMLを送信し、
    URLとタイトルも更新します。

    Args:
        consumer: WebSocketコンシューマーインスタンス
        content: クライアントから送信されたデータ
    """
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
    """
    新規ボード作成フォームを表示する。

    ボード一覧ページに新規作成フォームを追加した状態で
    HTMLを再レンダリングして送信します。

    Args:
        consumer: WebSocketコンシューマーインスタンス
        content: クライアントから送信されたデータ
    """
    context = get_boards_context(show_new_board_form=True)
    html = render_to_string("web/pages/boards.html", context)
    data = {
        "target": "#main",
        "html": html,
    }
    send(consumer, data)


@liveview_handler("boards->show_edit")
def show_edit(consumer, content):
    """
    ボード編集フォームを表示する。

    指定されたボードの編集フォームを表示した状態で
    HTMLを再レンダリングして送信します。

    Args:
        consumer: WebSocketコンシューマーインスタンス
        content: クライアントから送信されたデータ（board_idを含む）
    """
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
    """
    新規ボードを作成する。

    フォームから送信されたボード名で新規ボードを作成し、
    全クライアントに更新をブロードキャストします。

    Args:
        consumer: WebSocketコンシューマーインスタンス
        content: クライアントから送信されたデータ（フォームデータを含む）
    """
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
    """
    ボード名を更新する。

    指定されたボードの名前を更新し、
    全クライアントに更新をブロードキャストします。

    Args:
        consumer: WebSocketコンシューマーインスタンス
        content: クライアントから送信されたデータ（board_idとフォームデータを含む）
    """
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
    """
    ボードを削除する。

    指定されたボードを削除し、
    全クライアントに更新をブロードキャストします。
    ボードに紐づくリストとカードも連鎖的に削除されます。

    Args:
        consumer: WebSocketコンシューマーインスタンス
        content: クライアントから送信されたデータ（board_idを含む）
    """
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
