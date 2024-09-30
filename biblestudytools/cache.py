import gzip
import os

from .conf import PROG


def home():
    return os.environ.get("HOME")


class Data:
    path = f"{home()}/.{PROG}"

    def make_translation(translation: str):
        path = f"{Data.path}/{translation}"
        try:
            os.mkdir(path)
        except FileExistsError:
            pass

    def make_book(translation: str, book: str):
        path = f"{Data.path}/{translation}/{book}"
        try:
            os.mkdir(path)
        except FileExistsError:
            pass

    def save_chapter(
        translation: str, book: str, chapter: str, content: bytes
    ):
        path = f"{Data.path}/{translation}/{book}/{chapter}"
        with gzip.open(path, "wb") as fh:
            fh.write(content)

    def read_chapter(translation: str, book: str, chapter: str) -> bytes:

        if not os.path.exists(f"{Data.path}/{translation}"):
            Data.make_translation(translation)
        if not os.path.exists(f"{Data.path}/{translation}/{book}"):
            Data.make_book(translation, book)

        path = f"{Data.path}/{translation}/{book}/{chapter}"
        if not os.path.exists(path):
            return None

        with gzip.open(path, "rb") as fh:
            data = fh.read()
        return data
