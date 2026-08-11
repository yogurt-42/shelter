"""Shelter — item definitions.

Items are distinct from resources: they are rarer, often plot-related or equipment,
and share a single slot cap across all item types.
Each item unit occupies one slot.
"""

ITEM_DEFINITIONS = {
    "test_item_a": {
        "key": "test_item_a",
        "name": "测试物品 A",
        "description": "用于测试物品系统的占位道具。",
    },
    "test_item_b": {
        "key": "test_item_b",
        "name": "测试物品 B",
        "description": "另一个用于测试物品系统的占位道具。",
    },
}


def get_item(key: str) -> dict | None:
    """Look up an item template by key."""
    return ITEM_DEFINITIONS.get(key)


def list_items() -> list[dict]:
    """Return all defined item templates."""
    return list(ITEM_DEFINITIONS.values())
