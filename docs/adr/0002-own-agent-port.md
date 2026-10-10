# The agent sits behind our own port, not LangChain's chat model

The chat talks to the character agent through an `Agent` port that
takes the user's text and returns a reply. The LangChain chat model,
its Anthropic integration and the tool-calling loop live only in the
adapter, so the core, the CLI and the tests never see LangChain
types. We chose this over exposing `BaseChatModel` in the port
because the provider must stay swappable (Anthropic today) and
`CLAUDE.md` keeps ports free of LangChain types beyond `Document`.
It costs a little more adapter code and means the tool loop is not
shared across providers for free.
