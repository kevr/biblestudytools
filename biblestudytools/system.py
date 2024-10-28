import os
import random
import string
import sys
from subprocess import PIPE, Popen
from typing import Any


def execute(
    command: str,
    *args: list[str],
    input_data: str = False,
) -> int:
    cmd = [command] + list(args)
    proc = Popen(
        cmd,
        stdin=PIPE,
        stdout=PIPE,
        env=dict(os.environ),
    )
    data = input_data.encode() if input_data else None
    stdout = None
    try:
        stdout, _ = proc.communicate(input=data, timeout=1)
        stdout = stdout.decode()
    except Exception:
        pass

    if proc.returncode != 0:
        raise RuntimeError(f"{cmd} returned {proc.returncode}")

    return stdout


if __name__ == "__main__":
    e = 1

    letters = string.ascii_lowercase
    length = 12
    data = "".join(random.choice(letters) for i in range(length))

    e, stdout = execute("echo", data)
    print(stdout, end="")

    stdout = execute(
        "wl-copy",
        input_data=data,
    )
    stdout = execute(
        "wl-copy",
        "-p",
        input_data=data,
    )

    sys.exit(e)
