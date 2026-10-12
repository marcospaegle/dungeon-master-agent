from dungeon_core.tools.return_tool import ReturnTool


def test_the_outcome_is_taken_once():
    tool = ReturnTool()
    tool.return_to_concierge("The user wants an adventure.")

    assert tool.take() == "The user wants an adventure."
    assert tool.take() == ""


def test_nothing_is_taken_before_a_return():
    assert ReturnTool().take() == ""


def test_the_tool_is_named_for_the_model():
    names = [tool.name for tool in ReturnTool().tools()]

    assert names == ["return_to_concierge"]
