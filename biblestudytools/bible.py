import os
import re
from urllib.parse import quote_plus

from . import http
from .algorithm import parse_passages
from .cache import Data
from .conf import BASE_URI
from .translation import Translation


class Bible:
    def __init__(self, translation: str = "nkjv") -> "Bible":
        self.translation = Translation(translation)
        self.translation.parse()

        # Prepare storage
        if not os.path.exists(Data.path):
            os.mkdir(Data.path)

        self.num_results = 99
        self.num_chapters = None

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

        parent = '//div[@id="tabContent"]/div'

        num_results = root.xpath(
            parent + '/div[contains(@class, "text-gray-800")]/' "text()"
        )[0].strip()
        m = re.match(r"^Found (\d+) Results for$", num_results)
        self.num_results = int(m.group(1))

        results = root.xpath(parent + '/div[contains(@class, "shadow-md")]')
        output = []
        for result in results:
            title = result.xpath("./a")
            title = "".join([t.strip() for t in title[0].itertext()])
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
        """Number of chapters in a book."""
        if self.num_chapters is not None:
            return self.num_chapters

        path = self.book_uri(book) + "/chapters"
        if os.path.exists(path):
            with open(path) as f:
                self.num_chapters = int(f.read().strip())
            return self.num_chapters

        return None

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

    def download(self):
        """Download the whole Bible."""
        books = self.books()
        for book_display, book in books:
            nc = self.chapters(book)
            self.num_chapters = None

            for i in range(1, nc - 1):
                if self.chapter_exists(book, i):
                    continue

                try:
                    self.get_chapter(book, i)
                except http.HttpError:
                    num_chapters = i - 1
                    self.save_chapters(book, str(num_chapters))
                    print(f"Downloaded '{book_display}'")
                    break
