from collections.abc import Iterator
from contextlib import contextmanager

from rich.console import Console

console = Console(force_terminal=True)


@contextmanager
def spinner(text: str) -> Iterator[None]:
    with console.status(text, spinner="dots12"):
        yield
