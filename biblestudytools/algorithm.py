import re
from typing import Any, Callable

def reduce(array: list[Any], check: Callable) -> list[Any]:
    value = []
    for item in array:
        if check(item):
            value.append(item)
    return value

def regex_search(expr: str, array: list[tuple[str, str]],
                 flags: int = re.IGNORECASE) -> list[tuple[str, str]]:
    return reduce(array, lambda x: re.search(expr, x[0], flags))
