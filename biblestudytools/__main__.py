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
import re
from .bible import Bible
from .getch import getch
from .book import Chapter
from .conf import PROG
from .ui import BookUI

SOURCE = "https://biblestudytools.com"
HOME = os.environ.get("HOME")

logging.basicConfig(filename="/tmp/bst.log", level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s:%(message)s')


def parse_args():
    parser = argparse.ArgumentParser(prog=PROG,
                                     description=f"Cache client for {SOURCE}")

    parser.add_argument("-t", "--translation", default="nkjv")
    parser.add_argument("book")

    if "books" in sys.argv:
        args = parser.parse_args()
        return {
            "translation": args.translation,
            "book": args.book,
            "chapter": None,
            "verse": None,
        }

    parser.add_argument("verse")
    args = parser.parse_args()

    ch = 0  # Chapter
    verse = None  # Verse
    if ':' in args.verse:
        ch, verse = args.verse.split(':')
        ch = int(ch)
        if '-' in verse:
            verse = verse.split('-')
            try:
                start, end = [int(x) for x in verse]
            except Exception:
                raise argparse.ArgumentError(
                    f"invalid verse specification '{args.verse}'")

            if start < 1 or start > end:
                raise argparse.ArgumentError(
                    "invalid verse range; a >= 1 && b >= a")

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
    if '-' not in verses:
        i = int(verses)
        return (i, i)

    start, end = verses.split('-')
    return (
        int(start),
        int(end),
    )


def wait_for_input(chapter: int) -> int:
    """
    print("Press ", end='')
    if chapter > 1:
        print("'w' for previous, ", end='')
    print("'e' for next, or 'q' to exit... ", end='')
    sys.stdout.flush()
    """
    char = getch()
    if char == 'q':
        sys.exit(0)
    elif chapter > 1 and char == 'w':
        chapter -= 1
    elif char == 'e':
        chapter += 1
    return chapter


def output_chapter(chapter: Chapter, verses: tuple[int, int]):
    start, end = verses
    print(f"\n <---> {chapter.title}:{start}-{end} <--->\n")
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


BLUE_BG = 1


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
    if book == "books":
        for title, spec in books:
            print(f"{title}: {spec}")
        return 0

    for title, spec in books:
        if re.search(args.get("book"), title, re.IGNORECASE):
            book = spec
            break

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
