from lxml import etree

from .algorithm import parse_passages


class Chapter:
    def __init__(self, content: str) -> "Chapter":
        self.content = content
        self.parse(self.content)

    def parse(self, content: str):
        parser = etree.HTMLParser(recover=True)
        root = etree.fromstring(content, parser)

        h1 = root.xpath("//div/h1[contains(@class, 'text-xl')]")
        title = "".join(h1[0].itertext()).strip()
        if title == "Page not found":
            raise Exception("Page not found")

        self.title = title
        self.verses = parse_passages(root)

    def range(self) -> tuple[int, int]:
        return (1, len(self.verses))

    def lines(self):
        output = []
        for vl in self.verses:
            for v in vl:
                output.append(v)
        return output
