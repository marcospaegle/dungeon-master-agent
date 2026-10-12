from langchain_core.documents import Document

from dungeon_core.knowledge.ports.retriever import IndexNotBuiltError
from dungeon_core.tools.rules_search import RulesSearchTool


class FakeRetriever:
    def __init__(self, hits=(), error=None) -> None:
        self._hits = list(hits)
        self._error = error

    def check(self) -> None:
        pass

    def search(self, query: str, k: int):
        if self._error:
            raise self._error
        return self._hits


def test_results_name_their_source_and_page():
    hit = Document(
        page_content="Fighters wear any armor.",
        metadata={"source": "phb.pdf", "page": 94},
    )

    result = RulesSearchTool(FakeRetriever([hit])).search_rules("armor")

    assert result == "[phb.pdf, page 94]\nFighters wear any armor."


def test_a_missing_index_is_told_to_the_agent_not_raised():
    tool = RulesSearchTool(FakeRetriever(error=IndexNotBuiltError("Build!")))

    assert tool.search_rules("armor") == "Build!"


def test_it_offers_one_tool():
    [tool] = RulesSearchTool(FakeRetriever()).tools()

    assert tool.name == "search_rules"
