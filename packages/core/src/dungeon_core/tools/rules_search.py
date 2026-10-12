from langchain_core.tools import BaseTool, StructuredTool

from dungeon_core.knowledge.ports.retriever import (
    IndexNotBuiltError,
    Retriever,
)

SEARCH_RESULTS = 4


class RulesSearchTool:
    """Lets an Agent look the rules up in the indexed Sources."""

    def __init__(self, retriever: Retriever) -> None:
        self._retriever = retriever

    def tools(self) -> list[BaseTool]:
        return [StructuredTool.from_function(self.search_rules)]

    def search_rules(self, query: str) -> str:
        """Search the rulebooks; results name their Source and Page."""
        try:
            hits = self._retriever.search(query, SEARCH_RESULTS)
        except IndexNotBuiltError as error:
            return str(error)
        return "\n\n".join(
            f"[{hit.metadata['source']}, page {hit.metadata['page']}]\n"
            f"{hit.page_content}"
            for hit in hits
        )
