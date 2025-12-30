from asgiref.sync import async_to_sync
from channels.db import database_sync_to_async
from channels.layers import get_channel_layer

from web.models import Board
from web.utils import get_global_context, get_html

template = "web/pages/boards.html"


@database_sync_to_async
def get_all_boards():
    return list(Board.objects.all())


@database_sync_to_async
def create_board(name: str) -> Board:
    return Board.objects.create(name=name)


@database_sync_to_async
def update_board(board_id: int, name: str) -> Board | None:
    try:
        board = Board.objects.get(id=board_id)
        board.name = name
        board.save()
        return board
    except Board.DoesNotExist:
        return None


@database_sync_to_async
def delete_board(board_id: int) -> bool:
    try:
        board = Board.objects.get(id=board_id)
        board.delete()
        return True
    except Board.DoesNotExist:
        return False


async def get_context() -> dict:
    context = get_global_context()
    context.update(
        {
            "title": "ボード一覧 | Trello風TODOアプリ",
            "boards": await get_all_boards(),
        }
    )
    return context


async def send_page(consumer, client_data, lang=None):
    """Send boards page."""
    my_context = await get_context()
    html = await get_html(template, my_context)
    data = {
        "action": client_data["action"],
        "selector": "#main",
        "html": html,
        "url": "/",
        "title": my_context["title"],
    }
    await consumer.send_html(data)


async def create(consumer, client_data, lang=None):
    """Create a new board."""
    name = client_data.get("data", {}).get("name", "").strip()
    if name:
        await create_board(name)
        await broadcast_boards_update()
    await send_page(consumer, client_data, lang)


async def update(consumer, client_data, lang=None):
    """Update a board."""
    board_id = client_data.get("data", {}).get("board_id")
    name = client_data.get("data", {}).get("name", "").strip()
    if board_id and name:
        await update_board(int(board_id), name)
        await broadcast_boards_update()
    await send_page(consumer, client_data, lang)


async def delete(consumer, client_data, lang=None):
    """Delete a board."""
    board_id = client_data.get("data", {}).get("board_id")
    if board_id:
        await delete_board(int(board_id))
        await broadcast_boards_update()
    await send_page(consumer, client_data, lang)


async def broadcast_boards_update():
    """Broadcast boards update to all connected clients."""
    channel_layer = get_channel_layer()
    my_context = await get_context()
    html = await get_html(template, my_context)
    data = {
        "action": "boards_update",
        "selector": "#main",
        "html": html,
    }
    await channel_layer.group_send(
        "broadcast", {"type": "send_data_to_frontend", "data": data}
    )
