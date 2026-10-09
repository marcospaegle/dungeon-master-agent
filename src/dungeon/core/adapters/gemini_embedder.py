from langchain_google_genai import GoogleGenerativeAIEmbeddings


class GeminiEmbedder:
    """Embeds texts with Google Gemini."""

    def __init__(self, api_key: str, model: str) -> None:
        self._client = GoogleGenerativeAIEmbeddings(
            model=model,
            google_api_key=api_key,
            task_type="RETRIEVAL_DOCUMENT",
        )

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        return self._client.embed_documents(texts)
