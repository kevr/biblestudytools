import curses

COLORS = {
    "highlight": (curses.COLOR_BLACK, curses.COLOR_BLUE),
    "default": (-1, -1),
}
COLOR_IDS = {
    "highlight": 1,
    "default": 2,
}

started = False


class Colors:
    pair_ids: dict[str, int]
    pairs: dict[str, tuple[int, int]]

    def __init__(self, pairs: list[tuple[str, tuple[int, int]]] = []):
        self.pair_ids, self.pairs = {}, {}
        global started
        started = True
        curses.start_color()
        curses.use_default_colors()

        for name, pair in COLORS.items():
            id_ = COLOR_IDS.get(name)
            curses.init_pair(id_, *pair)

    def id(self, name: str) -> int:
        return COLOR_IDS.get(name)

    def pair(self, name: str) -> tuple[int, int]:
        return COLORS.get(name)

    def decoration(name: str, attr: int = 0) -> int:
        return (
            (curses.color_pair(COLOR_IDS.get(name)) | attr) if started else 0
        )

    def default_color(attr: int = 0) -> int:
        return Colors.decoration("default", attr)

    def color(self, name: str, attr: int = 0) -> int:
        return Colors.decoration(name, attr)
