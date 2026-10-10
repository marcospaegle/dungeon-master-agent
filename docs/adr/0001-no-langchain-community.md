# Pipeline steps avoid langchain-community

The concrete pipeline steps in `core` use `pypdf` directly and the
standalone LangChain packages (`langchain-google-genai`,
`langchain-chroma`, `langchain-text-splitters`), never
`langchain-community`, whose integrations are deprecated. LangChain's
own tutorials read PDFs with `pypdf` too. The ports stay free of
LangChain types beyond `Document`, so any implementation can be
replaced without touching `IndexingService`.
