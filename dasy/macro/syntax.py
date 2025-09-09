from dataclasses import dataclass
from itertools import count
from typing import Any, Callable

from hy import models


_gens = count(1)


@dataclass(frozen=True)
class Syntax:
    datum: Any
    scopes: tuple[int, ...] = ()


def is_sym(sx: "Syntax", name: str | None = None) -> bool:
    return isinstance(sx.datum, models.Symbol) and (
        name is None or str(sx.datum) == name
    )


def add_mark(sx: "Syntax", mark: int) -> "Syntax":
    return Syntax(sx.datum, (*sx.scopes, mark))


def same_id(a: "Syntax", b: "Syntax") -> bool:
    return (
        isinstance(a.datum, models.Symbol)
        and isinstance(b.datum, models.Symbol)
        and (a.datum == b.datum)
        and (a.scopes == b.scopes)
    )


def datum(sx: "Syntax"):
    return sx.datum


def gensym(prefix: str = "g__") -> models.Symbol:
    return models.Symbol(f"{prefix}{next(_gens)}")


class MacroEnv:
    def __init__(self):
        # stack of {str(name) -> transformer}
        self.frames: list[dict[str, Callable]] = [{}]

    def define(self, name: str, transformer: Callable):
        self.frames[-1][name] = transformer

    def lookup(self, name: str):
        for fr in reversed(self.frames):
            if name in fr:
                return fr[name]
        return None

    def push(self):
        self.frames.append({})

    def pop(self):
        self.frames.pop()
