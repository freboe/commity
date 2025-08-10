from rich.console import Console

console = Console()

def spinner(text: str):
    return console.status(text, spinner="dots12")
