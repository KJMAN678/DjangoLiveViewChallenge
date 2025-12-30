from asgiref.sync import sync_to_async
from django.template.loader import render_to_string


async def get_html(template: str, context: dict | None = None) -> str:
    """Get html from template."""
    if context is None:
        context = {}
    return await sync_to_async(render_to_string)(template, context)


def get_global_context() -> dict:
    """Get global context for templates."""
    return {}
