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
    num_verses = 0
    for div in divs:
        offset = 1

        title = div.xpath("./h3")
        if title:
            offset = 2
            title = title[0].xpath("./text()")[0]

        verse_num = div.xpath("./a/text()")[0].strip()

        i += 1
        indent = " " * (1 + len(str(i)))

        # Text sanitization for display
        body = [t.strip() for t in div.itertext()]
        body = [x for x in body if x]
        body = [verse_num] + body[offset:]

        text = re.sub(r"\s{2}", " ", " ".join(body))
        text = re.sub(r" ([:?,])", r"\1", text)

        if title:
            w = wrap(title, width=textwidth, subsequent_indent="")
            output += [[""], w, [""]]

        output.append(wrap(text, width=textwidth, subsequent_indent=indent))
        num_verses += 1

    return (num_verses, output)


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
