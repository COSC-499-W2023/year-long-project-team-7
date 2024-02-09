from django import template
import json

register = template.Library()


@register.filter
def get_item(dictionary: str, key: str) -> str:
    return str(json.loads(dictionary).get(key))
