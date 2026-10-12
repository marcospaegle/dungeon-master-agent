from collections.abc import Callable, Sequence

from dungeon_core.chat.command import Command, Reply

HINT = "Type /help to list the Commands."


class Chat:
    """A Chat: reads lines until /quit or the end of input.

    It dispatches to the Commands it is given and keeps the active
    Command, which gets every line that is not itself a Command. It
    owns /help, /exit and /quit; everything else is a Command.

    Input and output are injected so the Chat can be driven without a
    terminal. The read callable raises EOFError when input runs out.
    Everything written is Markdown.
    """

    def __init__(
        self,
        read: Callable[[], str],
        write: Callable[[str], None],
        commands: Sequence[Command] = (),
    ) -> None:
        self._read = read
        self._write = write
        self._commands = {command.name: command for command in commands}
        self._active: Command | None = None
        self._running = False
        self._builtins = {
            "/help": ("List the Commands", self._help),
            "/exit": ("Leave the active Command", self._exit),
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
        if not line.startswith("/"):
            if self._active is not None:
                self._show(self._active, self._active.handle(line))
            elif line:
                self._write(HINT)

            return

        name = line.split()[0]
        if name in self._builtins:
            _, handler = self._builtins[name]
            handler()
        elif name not in self._commands:
            self._write(f"Unknown Command: {name}\n\n{HINT}")
        elif self._active is not None:
            self._write(f"Already in {self._active.name}. /exit leaves.")
        else:
            command = self._commands[name]
            self._show(command, command.start())

    def _show(self, command: Command, reply: Reply) -> None:
        self._active = command if reply.active else None
        if reply.text:
            self._write(reply.text)

    def _help(self) -> None:
        described = [
            (name, text) for name, (text, _) in self._builtins.items()
        ] + [(c.name, c.description) for c in self._commands.values()]
        lines = [f"- `{name}` {text}" for name, text in described]
        self._write("\n".join(["Commands:", "", *lines]))

    def _exit(self) -> None:
        if self._active is None:
            self._write("Not in a Command.")

            return

        command, self._active = self._active, None
        self._show(command, command.leave())

    def _quit(self) -> None:
        self._running = False
