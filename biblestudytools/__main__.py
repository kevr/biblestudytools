"""
https://biblestudytools.com/nkjv New King James Version Bible scraper.

This script scrapes bible chapters from biblestudytools.com
and stores them in $HOME/.biblestudytools for subsequent
references.

Author: kevr
"""

import argparse
import logging
import logging.config
import os
import shutil
import sys
import traceback

from .algorithm import regex_search
from .bible import Bible
from .book import Chapter
from .conf import BASE_URI, PROG
from .http import HttpError
from .system import execute
from .ui import BookUI

HOME = os.environ.get("HOME")
SEARCH_BOOKS = {
    # Books
    "matthew": "mt",
    "mark": "mr",
    "luke": "lu",
    "john": "joh",
    "acts": "ac",
    "romans": "ro",
    "1 corinthians": "1co",
    "2 corinthians": "2co",
    "galatians": "ga",
    "ephesians": "eph",
    "1 peter": "1pe",
    "2 peter": "2pe",
    "1 john": "1jo",
    "2 john": "2jo",
    "3 john": "3jo",
    # Specific ranges
    "old": "o",
    "ot": "o",
    "new": "n",
    "nt": "n",
    "gospels": "gos",
}

logging.basicConfig(
    filename="/tmp/bst.log",
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s:%(message)s",
)


def make_optional_parser() -> argparse.ArgumentParser:
    epilog = "To list available books, run 'biblestudytools list'"
    parser = argparse.ArgumentParser(
        prog=PROG, description=f"Cache client for {BASE_URI}", epilog=epilog
    )

    parser.add_argument(
        "-t",
        "--translation",
        default="nkjv",
        help="Bible translation (default: 'nkjv')",
    )
    parser.add_argument(
        "-r",
        "--raw",
        default=False,
        action="store_true",
        help="Produce raw output (without ANSI escape codes)",
    )
    parser.add_argument(
        "-c",
        "--clipboard",
        default=False,
        action="store_true",
        help="Copy output to clipboard",
    )
    parser.add_argument(
        "book",
        help="regex matched against books "
        "returned by 'biblestudytools list'",
    )
    return parser


def parse_args():
    parser = make_optional_parser()

    if "list" in sys.argv or "download" in sys.argv:
        args = parser.parse_args()
        return {
            "translation": args.translation,
            "raw": args.raw,
            "clipboard": args.clipboard,
            "b": b,
            "book": args.book,
        }
    elif "search" in sys.argv:
        parser.add_argument(
            "-b",
            "--book",
            dest="b",
            type=str.lower,
            help="Particular book(s) to search",
        )
        parser.add_argument(
            "query", nargs="+", help="Keyword strings (space-separated)"
        )
        args = parser.parse_args()

        b = None
        if args.b:
            for key in SEARCH_BOOKS.keys():
                if key.startswith(args.b):
                    b = SEARCH_BOOKS.get(key)
                    print(f"Focusing search on '{key}'...\n")
                    break

            if b is None:
                raise LookupError(
                    f"error: no book '{args.b}' available to search"
                )

        return {
            "translation": args.translation,
            "raw": args.raw or args.clipboard,
            "clipboard": args.clipboard,
            "b": b,
            "book": args.book,
            "query": args.query,
        }

    parser.add_argument(
        "verse",
        help="chapter and optional verse range, " "e.g. 1, 3:16, 1:2-4",
    )
    args = parser.parse_args()

    ch = 0  # Chapter
    verse = None  # Verse
    if ":" in args.verse:
        ch, verse = args.verse.split(":")
        ch = int(ch)
        if "-" in verse:
            verse = verse.split("-")
            try:
                start, end = [int(x) for x in verse]
            except Exception:
                raise argparse.ArgumentError(
                    f"invalid verse specification '{args.verse}'"
                )

            if start < 1 or start > end:
                raise argparse.ArgumentError(
                    "invalid verse range; a >= 1 && b >= a"
                )

            verse = (start, end)
        else:
            verse = int(verse)
            verse = (verse, verse)
    else:
        ch = int(args.verse)

    return {
        "translation": args.translation,
        "raw": args.raw or args.clipboard,
        "clipboard": args.clipboard,
        "book": args.book,
        "chapter": ch,
        "verse": verse,
    }


def parse_range(verses: str) -> tuple[int, int]:
    if "-" not in verses:
        i = int(verses)
        return (i, i)

    start, end = verses.split("-")
    return (
        int(start),
        int(end),
    )


def print_append(memo: list[str], text: str):
    print(text)
    memo.append(text)


def output_chapter(
    chapter: Chapter,
    verses: tuple[int, int],
    raw: bool = False,
    clipboard: bool = False,
):
    start, end = verses
    verse_disp = f"{start}-{end}"
    if start == end:
        verse_disp = str(start)

    pre, post = "", ""
    if not raw:
        pre = "\n \033[1;4m"
        post = "\033[0m"

    t = chapter.translation.upper()
    memo = list()
    print_append(memo, f"{pre}{chapter.title}:{verse_disp} ({t}){post}\n")

    m = start - 1
    for i in range(start - 1, end):
        while not chapter.verses[m][1][0].startswith(f"{i + 1} "):
            m += 1
        attr, lines = chapter.verses[m]
        for line in lines:
            print_append(memo, line)

    if clipboard:
        memo_str = "\n".join(memo)
        execute("wl-copy", input_data=memo_str)
        execute("wl-copy", "-p", input_data=memo_str)
    else:
        print()


def single_view(
    bible: Bible,
    book: str,
    ch: int,
    verses: tuple[int, int],
    raw: bool,
    clipboard: bool,
):
    content = bible.get_chapter(book, ch)
    chapter = Chapter(bible.translation.name, content, raw)

    if not verses:
        verses = chapter.range()

    output_chapter(chapter, verses, raw, clipboard)


def get_lines(chapter: Chapter):
    lines = []
    for vl in chapter.verses:
        for v in vl:
            lines.append(v)
    return lines


def book_view(
    bible: Bible,
    book: str,
    ch: int,
    verses: tuple[int, int],
    raw: bool,
    clipboard: bool,
):
    ui = BookUI()
    ui.loop(bible, book, ch)


def search(args: dict[str, str], bible: Bible):
    page = 1
    while True:
        try:
            results = bible.search(args, page)
        except HttpError as exc:
            return 0
        page += 1

        ts = shutil.get_terminal_size((80, 20))
        textwidth = int(ts.columns * 0.9)
        print("#" * textwidth)
        for title, passage in results:
            print(f" - {title}")
            for attr, lines in passage:
                print("\n".join(lines))
            print()

        remaining = bible.num_results - (page * 20)
        if remaining < 1:
            break

        try:
            print(f"Remaining results: {remaining}")
            input("Press enter for more or CTRL+C to quit...")
            print()
        except KeyboardInterrupt:
            break

    return 0


def main():
    try:
        args = parse_args()
    except argparse.ArgumentError as exc:
        print(exc)
        return 1

    try:
        bible = Bible(args.get("translation"))
    except HttpError as exc:
        print(f"error: {exc}")
        return 1

    book = args.get("book")
    books = bible.books()
    if book == "list":
        print(", ".join([t[0] for t in books]))
        return 0
    elif book == "search":
        return search(args, bible)
    elif book == "download":
        bible.download()
        return 0

    results = regex_search(args.get("book"), books)
    if not results:
        print("error: invalid book name")
        return 1
    book = results[0][1]

    ch = args.get("chapter")
    verses = args.get("verse")

    is_oneshot = verses is not None
    f = {
        True: single_view,
        False: book_view,
    }

    try:
        f.get(is_oneshot)(
            bible, book, ch, verses, args.get("raw"), args.get("clipboard")
        )
    except Exception as exc:
        logging.error(exc)
        logging.error(traceback.format_exc())

    return 0


if __name__ == "__main__":
    e = 1
    try:
        e = main()
    except Exception as exc:
        print(f"error: {exc}")
    except HttpError as exc:
        print(f"error: {exc}")
    sys.exit(e)
