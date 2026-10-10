from collections.abc import Callable

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
        self._running = False
        self._commands = {
            "/help": ("List the Commands", self._help),
            "/quit": ("End the Chat", self._quit),
        }

    def run(self) -> None:
        self._running = True
        while self._running:
            try:
                line = self._read().strip()
            except EOFError:
                return
            self._handle(line)

    def _handle(self, line: str) -> None:
        if not line:
            return
        if not line.startswith("/"):
            self._write(HINT)
            return
        name = line.split()[0]
        if name not in self._commands:
            self._write(f"Unknown Command: {name}\n{HINT}")
            return
        _, handler = self._commands[name]
        handler()

    def _help(self) -> None:
        lines = [
            f"  {name}  {text}" for name, (text, _) in self._commands.items()
        ]
        self._write("\n".join(["Commands:", *lines]))

    def _quit(self) -> None:
        self._running = False
