from collections.abc import Callable

COMMANDS = {
    "/help": "List the Commands",
    "/quit": "End the Chat",
}

HINT = "Type /help to list the Commands."


class Chat:
    """A Chat: reads lines until a Command ends it.

    Input and output are injected so the Chat can be driven without a
    terminal. The read callable raises EOFError when input runs out.
    """

    def __init__(
        self,
        read: Callable[[], str],
        write: Callable[[str], None],
    ) -> None:
        self._read = read
        self._write = write

    def run(self) -> None:
        while True:
            try:
                line = self._read().strip()
            except EOFError:
                return
            if line == "/quit":
                return
            self._handle(line)

    def _handle(self, line: str) -> None:
        if not line:
            return
        if line == "/help":
            self._write(self._help())
        elif line.startswith("/"):
            name = line.split()[0]
            self._write(f"Unknown Command: {name}\n{HINT}")
        else:
            self._write(HINT)

    @staticmethod
    def _help() -> str:
        lines = [f"  {name}  {text}" for name, text in COMMANDS.items()]
        return "\n".join(["Commands:", *lines])
