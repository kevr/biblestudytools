import os
from urllib.parse import quote_plus
from . import http
from .cache import Data
from .conf import BASE_URI
from .translation import Translation
from .algorithm import parse_passages


class Bible:
    def __init__(self, translation: str = "nkjv") -> "Bible":
        self.translation = Translation(translation)
        self.translation.parse()

        # Prepare storage
        if not os.path.exists(Data.path):
            os.mkdir(Data.path)

    def search(self, criteria: str, p: int = 1):
        q = quote_plus(criteria)
        uri = f"{BASE_URI}/search"
        params = [
            ("t", self.translation),
            ("q", q),
            ("s", "bibles"),
            ("p", str(p)),
        ]
        urlparams = "&".join([f"{k}={v}" for k, v in params])
        content = http.get(f"{uri}?{urlparams}")

        root = http.parse(content.decode())
        results = root.xpath('//div[@id="tabContent"]/div/'
                             'div[contains(@class, "shadow-md")]')

        output = []
        for result in results:
            title = result.xpath('./a')
            title = ''.join([t.strip() for t in title[0].itertext()])
            passage = parse_passages(result)
            output.append((title, passage))
        return output

    def chapter_uri(self, book: str, chapter: int) -> str:
        return f"{BASE_URI}/{self.translation}/{book}/{chapter}.html"

    def book_uri(self, book: str) -> str:
        return f"{Data.path}/{self.translation}/{book}"

    def local_chapter_uri(self, book: str, chapter: int) -> str:
        return f"{Data.path}/{self.translation}/{book}/{chapter}"

    def chapter_exists(self, book: str, ch: int) -> bool:
        uri = self.local_chapter_uri(book, ch)
        return os.path.exists(uri)

    def books(self) -> list[tuple[str, str]]:
        return self.translation.books

    def chapters(self, book: str) -> int:
        """ Number of chapters in a book. """
        path = self.book_uri(book) + "/chapters"
        if os.path.exists(path):
            with open(path) as f:
                data = int(f.read().strip())
            return data

    def save_chapters(self, book: str, chapters: str):
        path = self.book_uri(book) + "/chapters"
        with open(path, "w") as f:
            f.write(chapters)

    def get_chapter(self, book: str, chapter: int) -> str:
        """
        Store and retrieve cached data originated from HTTP requests
        to the Bible.uri website
        """

        content = Data.read_chapter(self.translation, book, chapter)
        if not content:
            content = http.get(self.chapter_uri(book, chapter))
            Data.save_chapter(self.translation, book, chapter, content)
        return content.decode()
