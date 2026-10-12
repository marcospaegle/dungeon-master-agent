from collections.abc import Callable
from contextlib import AbstractContextManager, nullcontext

from dungeon_core.chat.chat import Chat


class Terminal:
    """Runs a Chat in a terminal: reads lines until /quit or the end.

    Input and output are injected so it can be driven without a real
    terminal. The read callable raises EOFError when input runs out.
    Everything written is Markdown. The busy callable returns a context
    manager held while the Chat works on a line, so a Frontend can show
    that the Agent is thinking.
    """

    def __init__(
        self,
        chat: Chat,
        read: Callable[[], str],
        write: Callable[[str], None],
        busy: Callable[[], AbstractContextManager] = nullcontext,
    ) -> None:
        self._chat = chat
        self._read = read
        self._write = write
        self._busy = busy

    def run(self) -> None:
        while not self._chat.ended:
            try:
                line = self._read()
            except EOFError:
                return
            with self._busy():
                reply = self._chat.send(line)
            if reply.text:
                self._write(reply.text)
