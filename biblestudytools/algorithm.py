import curses
import re
import shutil
from textwrap import wrap
from typing import Any, Callable

from lxml import etree

from .color import Colors


def _dec(content: list[str], attr: int = 0) -> tuple[int, list[str]]:
    return (attr, content)


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

        """ Needed for red-letter decoration. """
        # red = div.xpath("./span[contains(@class, 'red-letter')]")

        # Text sanitization for display
        body = [t.strip() for t in div.itertext()]
        body = [x for x in body if x]

        """ Red-letter attempt; good progress, need to persist between
            textwrapped lines.
        logging.info(body)
        for i in range(len(body)):
            for section in red:
                logging.info(section.text)
                # TODO: This doesn't work... because the red letter is
                # split upon multiple lines via textwrap.wrap
                # Think of a clever way to persist red-letter styles through
                # our output list along with textwrap.wrap results
                body[i] = body[i].replace(section.text, f"<{section.text}>")
        logging.info(f" * {body}")
        """

        body[offset] = body[offset].replace(str(verse_num), "")
        body = [verse_num] + body[offset:]

        text = re.sub(r"\s{2}", " ", " ".join(body))
        text = re.sub(r" ([:?,])", r"\1", text)

        if title:
            w = wrap(title, width=textwidth, subsequent_indent="")
            output += [
                _dec([""], Colors.default_color()),
                # Boldify segment titles
                _dec(w, Colors.default_color(curses.A_BOLD)),
                _dec([""], Colors.default_color()),
            ]

        output.append(
            _dec(
                wrap(text, width=textwidth, subsequent_indent=indent),
                Colors.default_color(),
            )
        )
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
