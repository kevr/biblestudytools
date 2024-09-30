import re
import shutil
from textwrap import wrap
from typing import Any, Callable

from lxml import etree


def parse_passages(root: etree._Element):
    ts = shutil.get_terminal_size((80, 20))
    textwidth = int(ts.columns * 0.9)
    divs = root.xpath(".//div[contains(@class, 'leading-8')]")
    i = 0
    output = []
    for div in divs:
        i += 1
        indent = " " * (2 + len(str(i)))

        # Text sanitization for display
        text = re.sub(
            r"\s{2}", " ", " ".join([t.strip() for t in div.itertext()])
        )
        text = re.sub(r" ([:?,])", r"\1", text)

        output.append(wrap(text, width=textwidth, subsequent_indent=indent))
    return output


def reduce(array: list[Any], check: Callable) -> list[Any]:
    value = []
    for item in array:
        if check(item):
            value.append(item)
    return value


def regex_search(
    expr: str, array: list[tuple[str, str]], flags: int = re.IGNORECASE
) -> list[tuple[str, str]]:
    return reduce(array, lambda x: re.search(expr, x[0], flags))
