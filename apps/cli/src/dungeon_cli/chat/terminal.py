from collections.abc import Callable

from dungeon_core.chat.chat import Chat


class Terminal:
    """Runs a Chat in a terminal: reads lines until /quit or the end.

    Input and output are injected so it can be driven without a real
    terminal. The read callable raises EOFError when input runs out.
    Everything written is Markdown.
    """

    def __init__(
        self,
        chat: Chat,
        read: Callable[[], str],
        write: Callable[[str], None],
    ) -> None:
        self._chat = chat
        self._read = read
        self._write = write

    def run(self) -> None:
        while not self._chat.ended:
            try:
                line = self._read()
            except EOFError:
                return
            reply = self._chat.send(line)
            if reply.text:
                self._write(reply.text)
