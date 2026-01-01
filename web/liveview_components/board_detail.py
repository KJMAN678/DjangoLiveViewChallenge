"""
ボード詳細ページのLiveViewハンドラモジュール

ボード詳細ページでのリスト・カードのCRUD操作と並び替えを
処理するWebSocketハンドラを定義します。
Django-LiveViewのliveview_handlerデコレータを使用して、
クライアントからのアクションに応答します。
"""

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
    """
    ボード詳細ページのコンテキストデータを取得する。

    Args:
        board_id: ボードID
        editing_board_name: ボード名編集フォームを表示するかどうか
        editing_list_id: 編集中のリストID
        editing_card_id: 編集中のカードID
        adding_card_to_list_id: カード追加フォームを表示するリストID
        show_add_list_form: リスト追加フォームを表示するかどうか

    Returns:
        dict: テンプレートに渡すコンテキスト辞書、ボードが存在しない場合はNone
    """
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
    """
    ボード詳細ページのHTMLをレンダリングする。

    Args:
        board_id: ボードID
        **kwargs: get_board_detail_contextに渡す追加引数

    Returns:
        str: レンダリングされたHTML文字列、ボードが存在しない場合はNone
    """
    context = get_board_detail_context(board_id, **kwargs)
    if context:
        return render_to_string("web/pages/board_detail.html", context)
    return None


def broadcast_board_update(consumer, board_id):
    """
    全クライアントにボード詳細の更新をブロードキャストする。

    同じWebSocketルームに接続している全クライアントに
    最新のボード詳細HTMLを送信します。

    Args:
        consumer: WebSocketコンシューマーインスタンス
        board_id: ボードID
    """
    html = render_board_detail_html(board_id)
    if html:
        data = {
            "target": "#main",
            "html": html,
        }
        consumer.broadcast_to_all(data)


@liveview_handler("board_detail->send_page")
def send_page(consumer, content):
    """
    ボード詳細ページを送信する。

    SPA遷移時にボード詳細ページのHTMLを送信し、
    URLとタイトルも更新します。

    Args:
        consumer: WebSocketコンシューマーインスタンス
        content: クライアントから送信されたデータ（board_idを含む）
    """
    data = content.get("data", {})
    board_id = data.get("board_id")
    if board_id:
        context = get_board_detail_context(board_id)
        if context:
            html = render_to_string("web/pages/board_detail.html", context)
            response_data = {
                "target": "#main",
                "html": html,
                "url": f"/board/{board_id}/",
                "title": context["title"],
            }
            send(consumer, response_data)


@liveview_handler("board_detail->show_edit_board_name")
def show_edit_board_name(consumer, content):
    """
    ボード名編集フォームを表示する。

    ボード名の編集フォームを表示した状態で
    HTMLを再レンダリングして送信します。

    Args:
        consumer: WebSocketコンシューマーインスタンス
        content: クライアントから送信されたデータ（board_idを含む）
    """
    payload = content.get("data", {})
    board_id = payload.get("board_id")
    if board_id:
        html = render_board_detail_html(board_id, editing_board_name=True)
        if html:
            send(consumer, {"target": "#main", "html": html})


@liveview_handler("board_detail->update_board_name")
def update_board_name(consumer, content):
    """
    ボード名を更新する。

    フォームから送信された新しいボード名でボードを更新し、
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
            broadcast_board_update(consumer, board_id)
        except Board.DoesNotExist:
            pass


@liveview_handler("board_detail->show_add_list_form")
def show_add_list_form(consumer, content):
    """
    リスト追加フォームを表示する。

    新規リスト追加フォームを表示した状態で
    HTMLを再レンダリングして送信します。

    Args:
        consumer: WebSocketコンシューマーインスタンス
        content: クライアントから送信されたデータ（board_idを含む）
    """
    payload = content.get("data", {})
    board_id = payload.get("board_id")
    if board_id:
        html = render_board_detail_html(board_id, show_add_list_form=True)
        if html:
            send(consumer, {"target": "#main", "html": html})


@liveview_handler("board_detail->add_list")
def add_list(consumer, content):
    """
    新規リストを追加する。

    フォームから送信されたリスト名で新規リストを作成し、
    全クライアントに更新をブロードキャストします。
    リストは末尾に追加されます。

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
            max_position = List.objects.filter(board=board).count()
            List.objects.create(board=board, name=name, position=max_position)
            broadcast_board_update(consumer, board_id)
        except Board.DoesNotExist:
            pass


@liveview_handler("board_detail->show_edit_list")
def show_edit_list(consumer, content):
    """
    リスト編集フォームを表示する。

    指定されたリストの編集フォームを表示した状態で
    HTMLを再レンダリングして送信します。

    Args:
        consumer: WebSocketコンシューマーインスタンス
        content: クライアントから送信されたデータ（board_idとlist_idを含む）
    """
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
            send(consumer, {"target": "#main", "html": html})


@liveview_handler("board_detail->edit_list")
def edit_list(consumer, content):
    """
    リスト名を更新する。

    フォームから送信された新しいリスト名でリストを更新し、
    全クライアントに更新をブロードキャストします。

    Args:
        consumer: WebSocketコンシューマーインスタンス
        content: クライアントから送信されたデータ（list_idとフォームデータを含む）
    """
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
    """
    リストを削除する。

    指定されたリストを削除し、全クライアントに更新をブロードキャストします。
    リストに含まれるカードも連鎖的に削除されます。

    Args:
        consumer: WebSocketコンシューマーインスタンス
        content: クライアントから送信されたデータ（list_idを含む）
    """
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
    """
    リストを左に移動する。

    指定されたリストの位置を1つ左（前）に移動し、
    全クライアントに更新をブロードキャストします。

    Args:
        consumer: WebSocketコンシューマーインスタンス
        content: クライアントから送信されたデータ（list_idを含む）
    """
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
    """
    リストを右に移動する。

    指定されたリストの位置を1つ右（後）に移動し、
    全クライアントに更新をブロードキャストします。

    Args:
        consumer: WebSocketコンシューマーインスタンス
        content: クライアントから送信されたデータ（list_idを含む）
    """
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
    """
    カード追加フォームを表示する。

    指定されたリストにカード追加フォームを表示した状態で
    HTMLを再レンダリングして送信します。

    Args:
        consumer: WebSocketコンシューマーインスタンス
        content: クライアントから送信されたデータ（board_idとlist_idを含む）
    """
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
            send(consumer, {"target": "#main", "html": html})


@liveview_handler("board_detail->add_card")
def add_card(consumer, content):
    """
    新規カードを追加する。

    フォームから送信されたカードタイトルで新規カードを作成し、
    全クライアントに更新をブロードキャストします。
    カードはリストの末尾に追加されます。

    Args:
        consumer: WebSocketコンシューマーインスタンス
        content: クライアントから送信されたデータ（list_idとフォームデータを含む）
    """
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
    """
    カード編集フォームを表示する。

    指定されたカードの編集フォームを表示した状態で
    HTMLを再レンダリングして送信します。

    Args:
        consumer: WebSocketコンシューマーインスタンス
        content: クライアントから送信されたデータ（board_idとcard_idを含む）
    """
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
            send(consumer, {"target": "#main", "html": html})


@liveview_handler("board_detail->edit_card")
def edit_card(consumer, content):
    """
    カードタイトルを更新する。

    フォームから送信された新しいタイトルでカードを更新し、
    全クライアントに更新をブロードキャストします。

    Args:
        consumer: WebSocketコンシューマーインスタンス
        content: クライアントから送信されたデータ（card_idとフォームデータを含む）
    """
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
    """
    カードを削除する。

    指定されたカードを削除し、全クライアントに更新をブロードキャストします。

    Args:
        consumer: WebSocketコンシューマーインスタンス
        content: クライアントから送信されたデータ（card_idを含む）
    """
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
    """
    カードを上に移動する。

    指定されたカードの位置を1つ上（前）に移動し、
    全クライアントに更新をブロードキャストします。

    Args:
        consumer: WebSocketコンシューマーインスタンス
        content: クライアントから送信されたデータ（card_idとlist_idを含む）
    """
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
    """
    カードを下に移動する。

    指定されたカードの位置を1つ下（後）に移動し、
    全クライアントに更新をブロードキャストします。

    Args:
        consumer: WebSocketコンシューマーインスタンス
        content: クライアントから送信されたデータ（card_idとlist_idを含む）
    """
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
