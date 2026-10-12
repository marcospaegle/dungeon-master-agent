from typing import NamedTuple, Protocol


class Reply(NamedTuple):
    """What a Command says back, as Markdown.

    ``active`` says whether the Command stays the active Command, so
    the next message is addressed to it. An empty text says nothing.
    """

    text: str
    active: bool = False


class Command(Protocol):
    """A chat Command, independent of the frontend that runs it.

    It takes messages and returns Replies; it never reads input
    itself, so a question it asks is answered by its next ``handle``.
    A frontend keeps one instance per conversation.
    """

    name: str
    description: str

    def start(self) -> Reply:
        """Run when the user types the Command."""
        ...

    def handle(self, text: str) -> Reply:
        """Take the text addressed to the active Command."""
        ...

    def leave(self) -> Reply:
        """Run when the user leaves the active Command."""
        ...
