import gzip
import os

from lxml import etree

from . import http
from .cache import Data
from .conf import BASE_URI


class Translation:
    def __init__(self, name: str) -> "Translation":
        self.name = name

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"<Translation:{self.name}>"

    def _parse_uri_leaf(self, element: etree._Element):
        href = element.attrib.get("href")
        return href.split("/")[-2]

    def _parse_display_name(self, element: etree._Element):
        return element.text.strip()

    def _parse_element(self, element: etree._Element) -> tuple[str, str]:
        return (
            self._parse_display_name(element),
            self._parse_uri_leaf(element),
        )

    def parse(self):
        local_uri = f"{Data.path}/{self.name}/books"
        content = None
        if os.path.exists(local_uri):
            with gzip.open(local_uri, "rb") as f:
                content = f.read()
        else:
            dp = "/".join(local_uri.split("/")[-1:])
            if not os.path.isdir(dp):
                os.mkdir(dp)

            uri = f"{BASE_URI}/{self.name}"
            content = http.get(uri)
            with gzip.open(local_uri, "wb") as f:
                f.write(content)

        parser = etree.HTMLParser(recover=True)
        root = etree.fromstring(content.decode(), parser)

        books = root.xpath("//div[contains(@class, 'grid-cols-2')]/div/a")
        self.books = [self._parse_element(b) for b in books]
        self.mapping = {el[0]: el[1] for el in self.books}
