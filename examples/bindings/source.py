"""A small program using closures, keyword calls, and Python's class machinery."""

from __future__ import annotations

import asyncio
import collections.abc
from os.path import basename

__all__ = ["render_report"]

total = 4


def make_counter(total, *, increment=2):
    def advance(factor=1):
        nonlocal total
        total += factor * increment
        return total

    return advance


class Counter:
    """Keep a counter through a name-mangled slot."""

    __slots__ = ("__value",)

    def __init__(self, value: int, /) -> None:
        self.__value = value

    def reading(self) -> int:
        return self.__value


class OffsetCounter(Counter):
    __slots__ = ()

    def reading(self) -> int:
        return super().reading() + 1


def bump_global():
    global total
    total += 1


async def render_report(*, filename: str = "reports/weekly.txt") -> tuple[str, ...]:
    advance = make_counter(total=total, increment=3)
    counter = OffsetCounter(advance(factor=2))
    bump_global()
    await asyncio.sleep(0)
    match [basename(filename), counter.reading()]:
        case ["weekly.txt", reading] if 4 < reading < 20:
            return basename(filename), str(reading), str(advance()), str(total)
        case _:
            return ("unexpected",)


if __name__ == "__main__":
    assert isinstance(render_report.__annotations__, collections.abc.Mapping)
    print(Counter.__doc__)
    print(asyncio.run(render_report(filename="archive/weekly.txt")))
