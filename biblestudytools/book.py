from lxml import etree

from .algorithm import parse_passages


class Chapter:
    def __init__(self, translation: str, content: str) -> "Chapter":
        self.translation = translation
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
        self.num_verses, self.verses = parse_passages(root)

    def range(self) -> tuple[int, int]:
        # TODO: Fix extra +1 verses in NIV acts 8, why?
        return (1, self.num_verses)

    def lines(self):
        output = []
        for vl in self.verses:
            for v in vl[1]:
                output.append((vl[0], v))
        return output
