from lxml import etree
from textwrap import wrap
import re
import shutil


class Chapter:
    def __init__(self, content: str) -> "Chapter":
        self.content = content
        self.parse(self.content)

    def parse(self, content: str):
        parser = etree.HTMLParser(recover=True)
        root = etree.fromstring(content, parser)

        h1 = root.xpath("//div/h1[contains(@class, 'text-xl')]")
        title = ''.join(h1[0].itertext()).strip()
        if title == "Page not found":
            raise Exception("Page not found")

        ts = shutil.get_terminal_size((80, 20))
        textwidth = int(ts.columns * 0.9)
        divs = root.xpath("//div[contains(@class, 'leading-8')]")
        i = 0
        output = []
        for div in divs:
            i += 1
            indent = ' ' * (2 + len(str(i)))

            # Text sanitization for display
            text = re.sub(r'\s{2}', ' ',
                          ' '.join([t.strip() for t in div.itertext()]))
            text = re.sub(r' ([:?,])', r'\1', text)

            output.append(
                wrap(text, width=textwidth, subsequent_indent=indent))

        self.title = title
        self.verses = output

    def range(self) -> tuple[int, int]:
        return (1, len(self.verses))

    def lines(self):
        output = []
        for vl in self.verses:
            for v in vl:
                output.append(v)
        return output
