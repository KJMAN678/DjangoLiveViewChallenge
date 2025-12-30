from channels.db import database_sync_to_async
from channels.layers import get_channel_layer

from web.models import Board, Card, List
from web.utils import get_global_context, get_html

template = "web/pages/board_detail.html"


@database_sync_to_async
def get_board(board_id: int) -> Board | None:
    try:
        return Board.objects.prefetch_related("lists__cards").get(id=board_id)
    except Board.DoesNotExist:
        return None


@database_sync_to_async
def create_list(board_id: int, name: str) -> List | None:
    try:
        board = Board.objects.get(id=board_id)
        max_position = board.lists.count()
        return List.objects.create(board=board, name=name, position=max_position)
    except Board.DoesNotExist:
        return None


@database_sync_to_async
def update_list(list_id: int, name: str) -> List | None:
    try:
        list_obj = List.objects.get(id=list_id)
        list_obj.name = name
        list_obj.save()
        return list_obj
    except List.DoesNotExist:
        return None


@database_sync_to_async
def delete_list(list_id: int) -> int | None:
    try:
        list_obj = List.objects.get(id=list_id)
        board_id = list_obj.board_id
        list_obj.delete()
        return board_id
    except List.DoesNotExist:
        return None


@database_sync_to_async
def create_card(list_id: int, title: str) -> Card | None:
    try:
        list_obj = List.objects.get(id=list_id)
        max_position = list_obj.cards.count()
        return Card.objects.create(list=list_obj, title=title, position=max_position)
    except List.DoesNotExist:
        return None


@database_sync_to_async
def update_card(card_id: int, title: str) -> Card | None:
    try:
        card = Card.objects.get(id=card_id)
        card.title = title
        card.save()
        return card
    except Card.DoesNotExist:
        return None


@database_sync_to_async
def delete_card(card_id: int) -> int | None:
    try:
        card = Card.objects.get(id=card_id)
        board_id = card.list.board_id
        card.delete()
        return board_id
    except Card.DoesNotExist:
        return None


@database_sync_to_async
def move_card(card_id: int, target_list_id: int, target_position: int) -> int | None:
    try:
        card = Card.objects.get(id=card_id)
        old_list = card.list
        board_id = old_list.board_id

        target_list = List.objects.get(id=target_list_id)

        if old_list.id == target_list.id:
            old_position = card.position
            if old_position < target_position:
                Card.objects.filter(
                    list=old_list,
                    position__gt=old_position,
                    position__lte=target_position,
                ).update(position=models.F("position") - 1)
            else:
                Card.objects.filter(
                    list=old_list,
                    position__gte=target_position,
                    position__lt=old_position,
                ).update(position=models.F("position") + 1)
        else:
            Card.objects.filter(list=old_list, position__gt=card.position).update(
                position=models.F("position") - 1
            )
            Card.objects.filter(
                list=target_list, position__gte=target_position
            ).update(position=models.F("position") + 1)
            card.list = target_list

        card.position = target_position
        card.save()
        return board_id
    except (Card.DoesNotExist, List.DoesNotExist):
        return None


@database_sync_to_async
def move_list(list_id: int, target_position: int) -> int | None:
    try:
        list_obj = List.objects.get(id=list_id)
        board = list_obj.board
        board_id = board.id
        old_position = list_obj.position

        if old_position < target_position:
            List.objects.filter(
                board=board,
                position__gt=old_position,
                position__lte=target_position,
            ).update(position=models.F("position") - 1)
        else:
            List.objects.filter(
                board=board,
                position__gte=target_position,
                position__lt=old_position,
            ).update(position=models.F("position") + 1)

        list_obj.position = target_position
        list_obj.save()
        return board_id
    except List.DoesNotExist:
        return None


async def get_context(board_id: int) -> dict:
    context = get_global_context()
    board = await get_board(board_id)
    if board:
        context.update(
            {
                "title": f"{board.name} | Trello風TODOアプリ",
                "board": board,
            }
        )
    return context


async def send_page(consumer, client_data, lang=None):
    """Send board detail page."""
    board_id = client_data.get("data", {}).get("board_id")
    if not board_id:
        from web.actions import boards

        await boards.send_page(consumer, client_data, lang)
        return

    my_context = await get_context(int(board_id))
    if not my_context.get("board"):
        from web.actions import boards

        await boards.send_page(consumer, client_data, lang)
        return

    html = await get_html(template, my_context)
    data = {
        "action": client_data["action"],
        "selector": "#main",
        "html": html,
        "url": f"/board/{board_id}/",
        "title": my_context["title"],
    }
    await consumer.send_html(data)


async def add_list(consumer, client_data, lang=None):
    """Add a new list to the board."""
    board_id = client_data.get("data", {}).get("board_id")
    name = client_data.get("data", {}).get("name", "").strip()
    if board_id and name:
        await create_list(int(board_id), name)
        await broadcast_board_update(int(board_id))
    client_data["data"]["board_id"] = board_id
    await send_page(consumer, client_data, lang)


async def edit_list(consumer, client_data, lang=None):
    """Edit a list."""
    list_id = client_data.get("data", {}).get("list_id")
    name = client_data.get("data", {}).get("name", "").strip()
    board_id = client_data.get("data", {}).get("board_id")
    if list_id and name:
        await update_list(int(list_id), name)
        if board_id:
            await broadcast_board_update(int(board_id))
    client_data["data"]["board_id"] = board_id
    await send_page(consumer, client_data, lang)


async def remove_list(consumer, client_data, lang=None):
    """Remove a list."""
    list_id = client_data.get("data", {}).get("list_id")
    board_id = client_data.get("data", {}).get("board_id")
    if list_id:
        result_board_id = await delete_list(int(list_id))
        if result_board_id:
            await broadcast_board_update(result_board_id)
            board_id = result_board_id
    client_data["data"]["board_id"] = board_id
    await send_page(consumer, client_data, lang)


async def add_card(consumer, client_data, lang=None):
    """Add a new card to a list."""
    list_id = client_data.get("data", {}).get("list_id")
    title = client_data.get("data", {}).get("title", "").strip()
    board_id = client_data.get("data", {}).get("board_id")
    if list_id and title:
        await create_card(int(list_id), title)
        if board_id:
            await broadcast_board_update(int(board_id))
    client_data["data"]["board_id"] = board_id
    await send_page(consumer, client_data, lang)


async def edit_card(consumer, client_data, lang=None):
    """Edit a card."""
    card_id = client_data.get("data", {}).get("card_id")
    title = client_data.get("data", {}).get("title", "").strip()
    board_id = client_data.get("data", {}).get("board_id")
    if card_id and title:
        await update_card(int(card_id), title)
        if board_id:
            await broadcast_board_update(int(board_id))
    client_data["data"]["board_id"] = board_id
    await send_page(consumer, client_data, lang)


async def remove_card(consumer, client_data, lang=None):
    """Remove a card."""
    card_id = client_data.get("data", {}).get("card_id")
    board_id = client_data.get("data", {}).get("board_id")
    if card_id:
        result_board_id = await delete_card(int(card_id))
        if result_board_id:
            await broadcast_board_update(result_board_id)
            board_id = result_board_id
    client_data["data"]["board_id"] = board_id
    await send_page(consumer, client_data, lang)


async def reorder_card(consumer, client_data, lang=None):
    """Reorder a card (drag and drop)."""
    card_id = client_data.get("data", {}).get("card_id")
    target_list_id = client_data.get("data", {}).get("target_list_id")
    target_position = client_data.get("data", {}).get("target_position", 0)
    board_id = client_data.get("data", {}).get("board_id")
    if card_id and target_list_id is not None:
        result_board_id = await move_card(
            int(card_id), int(target_list_id), int(target_position)
        )
        if result_board_id:
            await broadcast_board_update(result_board_id)
            board_id = result_board_id
    client_data["data"]["board_id"] = board_id
    await send_page(consumer, client_data, lang)


async def reorder_list(consumer, client_data, lang=None):
    """Reorder a list (drag and drop)."""
    list_id = client_data.get("data", {}).get("list_id")
    target_position = client_data.get("data", {}).get("target_position", 0)
    board_id = client_data.get("data", {}).get("board_id")
    if list_id is not None:
        result_board_id = await move_list(int(list_id), int(target_position))
        if result_board_id:
            await broadcast_board_update(result_board_id)
            board_id = result_board_id
    client_data["data"]["board_id"] = board_id
    await send_page(consumer, client_data, lang)


async def broadcast_board_update(board_id: int):
    """Broadcast board update to all connected clients."""
    channel_layer = get_channel_layer()
    my_context = await get_context(board_id)
    if my_context.get("board"):
        html = await get_html(template, my_context)
        data = {
            "action": "board_update",
            "selector": "#main",
            "html": html,
            "board_id": board_id,
        }
        await channel_layer.group_send(
            f"board_{board_id}", {"type": "send_data_to_frontend", "data": data}
        )


# Import models at the top level for F expressions
from django.db import models
