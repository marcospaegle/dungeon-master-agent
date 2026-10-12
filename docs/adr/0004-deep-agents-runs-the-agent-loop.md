# Deep Agents runs the Agent loop

Supersedes [0002](0002-own-agent-port.md).

Each Agent is a Deep Agents graph, built by a class in
`dungeon_core.agents`. We no longer own a tool-calling loop or an
`Agent` port that hides it: the loop, tool calls, interrupts and
conversation state (a checkpointer, with one thread per started Agent)
belong to the framework. The provider stays swappable because Deep
Agents accepts any LangChain chat model. Frontends never see it: they
talk to a `Chat`, which sends text in and returns Replies.

Each Agent gets only the Tools it is given: Deep Agents' built-in
filesystem, planning and sub-agent tools are excluded unless an Agent
opts in. User confirmation is an interrupt on the Tool (for example
`save_character`), not a step in a Command.

We chose this over keeping our own loop because the loop is not what
makes this project valuable, and a second Agent (the Dungeon Master)
would otherwise duplicate it. It costs coupling to a young framework.
LangChain remains in use for embeddings, the vector store and text
splitting (see [0001](0001-no-langchain-community.md)).
