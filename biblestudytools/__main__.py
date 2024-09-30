"""
https://biblestudytools.com/nkjv New King James Version Bible scraper.

This script scrapes bible chapters from biblestudytools.com
and stores them in $HOME/.biblestudytools for subsequent
references.

Author: kevr
"""

import os
import sys
import argparse
import logging
import logging.config
import traceback
from .bible import Bible
from .book import Chapter
from .conf import PROG, BASE_URI
from .ui import BookUI
from .algorithm import regex_search
from .http import HttpError

HOME = os.environ.get("HOME")

logging.basicConfig(
    filename="/tmp/bst.log",
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s:%(message)s",
)


def parse_args():
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
        "book",
        help="regex matched against books "
        "returned by 'biblestudytools list'",
    )

    if "list" in sys.argv:
        args = parser.parse_args()
        return {
            "translation": args.translation,
            "book": args.book,
            "chapter": None,
            "verse": None,
        }
    elif "search" in sys.argv:
        parser.add_argument("query")
        args = parser.parse_args()
        return {
            "translation": args.translation,
            "book": args.book,
            "chapter": None,
            "verse": None,
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


def output_chapter(chapter: Chapter, verses: tuple[int, int]):
    start, end = verses
    verse_disp = f"{start}-{end}"
    if start == end:
        verse_disp = str(start)

    print(f"\n <---> {chapter.title}:{verse_disp} <--->\n")
    for i in range(start - 1, end):
        for line in chapter.verses[i]:
            print(line)
        # print(chapter.verses[i])
    print()


def single_view(bible: Bible, book: str, ch: int, verses: tuple[int, int]):
    content = bible.get_chapter(book, ch)
    chapter = Chapter(content)

    if not verses:
        verses = chapter.range()

    output_chapter(chapter, verses)


def get_lines(chapter: Chapter):
    lines = []
    for vl in chapter.verses:
        for v in vl:
            lines.append(v)
    return lines


def book_view(bible: Bible, book: str, ch: int, verses: tuple[int, int]):
    ui = BookUI()
    ui.loop(bible, book, ch)


def main():
    try:
        args = parse_args()
    except argparse.ArgumentError as exc:
        print(exc)
        return 1

    bible = Bible(args.get("translation"))
    book = args.get("book")
    books = bible.books()
    if book == "list":
        print(", ".join([t[0] for t in books]))
        return 0
    elif book == "search":
        p = 1
        while True:
            try:
                results = bible.search(args.get("query"), p)
            except HttpError:
                break

            remaining = bible.num_results - (p * 20)
            p += 1

            for title, passage in results:
                print(f" - {title}")
                for lines in passage:
                    print("\n".join(lines))
                print()

            if remaining < 1:
                break

            try:
                print(f"Remaining results: {remaining}")
                input("Press enter for more or CTRL+C to quit...")
                print()
            except KeyboardInterrupt:
                break

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
        f.get(is_oneshot)(bible, book, ch, verses)
    except Exception as exc:
        logging.error(exc)
        logging.error(traceback.format_exc())

    return 0


if __name__ == "__main__":
    e = 1
    try:
        e = main()
    except Exception as exc:
        print(exc)
        e = 1
    sys.exit(1)
