import curses
import logging
import os
import sys
import threading

from .bible import Bible
from .book import Chapter
from .color import Colors
from .http import HttpError


class BookUI:
    c: Colors
    TITLEBAR_HEIGHT: int = 1

    back_running = True
    forward_running = True

    def __init__(self) -> "BookUI":
        # Instance-based counters
        self.resized = 0

        # Initialization
        self.stdscr = curses.initscr()
        curses.noecho()
        curses.curs_set(0)

        self.c = Colors()

        # Initialize input specifics
        self.stdscr.keypad(True)

        # Painting
        self.stdscr.refresh()

        self._init_layout(*self.stdscr.getmaxyx())

    def _init_layout(self, h: int, w: int):
        self.h, self.w = h, w
        o = self.TITLEBAR_HEIGHT

        self.titlebar = self.stdscr.derwin(o, w, 0, 0)
        self.titlebar.bkgd(" ", self.c.color("highlight", curses.A_BOLD))
        self.titlebar.refresh()

        self.pad = None

    def _paint_titlebar(self, verses: tuple[int, int]):
        # Rerender titlebar
        chapters = self.bible.chapters(self.book)

        title = self.chapter.title.split()
        num_chapter = title[-1]
        title = " ".join(title[:-1])

        lhs = f"{title}, {num_chapter}"
        if chapters is not None:
            lhs += f" of {chapters}"
        t = self.bible.translation.name.upper()
        title = f"{lhs} — vv. {verses[0]}-{verses[1]} ({t})"

        y, x = self.titlebar.getmaxyx()
        if x < len(title) + 2:
            return None

        self.titlebar.erase()
        lt = len(title)
        x = max(int(self.w / 2) - int(lt / 2) - int(not (lt % 2)), 0)
        self.titlebar.addstr(0, x, title)
        self.titlebar.refresh()

    def _init_pad(self):
        h, w = self.stdscr.getmaxyx()
        o = 1
        self.pad = self.stdscr.subpad(
            h - self.TITLEBAR_HEIGHT, w, self.TITLEBAR_HEIGHT, 0
        )
        self.pad.scrollok(1)

    def _paint_pad(self):
        y, x = self.pad.getmaxyx()
        if x <= 6:
            return None

        self.pad.erase()
        self.lines = self.chapter.lines()
        n = min(curses.LINES - 1, len(self.lines))
        for i in range(0, n):
            attr, line = self.lines[i]
            self.pad.addstr(i, 0, line, attr)
        self.pad.refresh()

        # Reset position to the top
        self.pos = 0
        self.i = n - 1

    def resize(self):
        self.pad.deleteln()
        self.titlebar.deleteln()
        y, x = self.stdscr.getmaxyx()
        curses.resizeterm(y, x)
        self.stdscr.clear()
        self.stdscr.refresh()

        self._init_layout(*self.stdscr.getmaxyx())

        return False

    def fetch_chapter(self, bible: Bible, book: str, ch: int):
        uri = bible.local_chapter_uri(book, ch)
        if not os.path.exists(uri):
            bible.get_chapter(book, ch)

    def __back_thread(self, bible: Bible, book: str, ch: int):
        try:
            for i in range(ch - 1, 0, -1):
                if not self.back_running:
                    return
                self.fetch_chapter(bible, book, i)
        except HttpError:
            return

    def __forward_thread(self, bible: Bible, book: str, ch: int):
        num_chapters = bible.chapters(book) or 200

        chap = None
        try:
            for i in range(ch + 1, num_chapters):
                if not self.forward_running:
                    return
                try:
                    self.fetch_chapter(bible, book, i)
                except HttpError:
                    # re-raise HttpError with our previous index
                    raise HttpError(str(i - 1))
        except HttpError as exc:
            # Save the raised index
            bible.save_chapters(book, str(exc))
            self._paint_titlebar(self.chapter.range())

    def _thread(self, fn, bible: Bible, book: str, ch: int):
        try:
            fn(bible, book, ch)
        except Exception as exc:
            logging.error(exc)

    def loop(self, bible: Bible, book: str, ch: int):
        self.bible = bible
        self.book = book
        self.ch = ch

        self.forward_thread = threading.Thread(
            target=self._thread,
            args=(self.__forward_thread, self.bible, book, ch),
        )
        self.forward_thread.start()

        self.back_thread = threading.Thread(
            target=self._thread,
            args=(self.__back_thread, self.bible, book, ch),
        )
        self.back_thread.start()

        while True:
            if self.pad is None:
                self._init_pad()

            try:
                content = self.bible.get_chapter(book, self.ch)
                self.chapter = Chapter(self.bible.translation.name, content)
            except HttpError as e:
                logging.error(e)
                curses.endwin()
                print(f"error: {e}")
                return None

            self.pad_h, self.pad_w = self.pad.getmaxyx()
            self._paint_titlebar(self.chapter.range())

            try:
                self._paint_pad()
            except curses.error:
                self.resize()
                continue

            self.input_loop()

    def input_loop(self):
        cb = {
            curses.KEY_UP: self._up,
            curses.KEY_PPAGE: self._page_up,
            curses.KEY_DOWN: self._down,
            curses.KEY_NPAGE: self._page_down,
            curses.KEY_LEFT: self._left,
            curses.KEY_RIGHT: self._right,
            curses.KEY_RESIZE: self._resize,
            ord("q"): self._quit,
        }

        while True:
            char = self.stdscr.getch()
            if char in cb:
                if not cb.get(char)():
                    break

    def _up(self, refresh: bool = True) -> bool:
        if self.pos == 0:
            # opt out, already at the top
            return True

        self.pad.scroll(-1)
        attr, line = self.lines[self.i - self.pad_h]
        self.pad.addstr(0, 0, line, attr)
        self.pos -= 1
        self.i -= 1

        if refresh:
            self.pad.refresh()

        return True

    def _page_up(self) -> bool:
        x = min(self.pad_h, self.pos)
        for i in range(x):
            self._up(refresh=False)
        self.pad.refresh()
        return True

    def _interval_n(self, y: int, direction: int = 1) -> bool:
        n_lines = len(self.lines)
        bottom_most = n_lines - self.pad_h

        if self.pad_h > n_lines or self.pos == bottom_most:
            return True

        yd = y * direction
        self.pad.scroll(yd)
        pos = self.pad_h - yd
        for i in range(y):
            self.i += 1 * direction
            attr, line = self.lines[self.i]
            self.pad.addstr(pos, 0, line, attr)
            pos += 1 * direction
        self.pos += yd
        self.pad.refresh()

        return True

    def _down(self) -> bool:
        self._interval_n(1)
        return True

    def _page_down(self) -> bool:
        remaining = (len(self.lines) - 1) - self.i
        x = min(self.pad_h, remaining)
        return self._interval_n(x)

    def _left(self) -> bool:
        if not self.bible.chapter_exists(self.book, self.ch - 1):
            return True
        self.ch -= 1
        return False

    def _right(self) -> bool:
        if not self.bible.chapter_exists(self.book, self.ch + 1):
            return True
        self.ch += 1
        return False

    def _resize(self) -> bool:
        self.resized += 1
        if self.resized % 2 == 0:
            self.resized = 0
            return True

        return self.resize()

    def _quit(self) -> bool:
        self.sync()
        sys.exit(0)
        return False

    def sync(self):
        self.back_running, self.forward_running = False, False
        try:
            self.back_thread.join()
        except Exception:
            pass
        try:
            self.forward_thread.join()
        except Exception:
            pass

    def __del__(self):
        self.sync()
        try:
            curses.endwin()
        except Exception:
            pass
