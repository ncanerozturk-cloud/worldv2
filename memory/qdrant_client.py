import os
import uuid
from typing import Optional

from dotenv import load_dotenv
from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

load_dotenv()

COLLECTION_NAME = "caneros_memory"
EMBEDDING_MODEL = "text-embedding-3-small"
VECTOR_SIZE = 1536


class QdrantMemory:
    def __init__(self):
        host = os.getenv("QDRANT_HOST", "localhost")
        port = int(os.getenv("QDRANT_PORT", 6333))
        self.client = QdrantClient(url=f"http://{host}:{port}")
        self.openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self._ensure_collection()

    def _ensure_collection(self):
        """Create the collection if it doesn't already exist."""
        existing = [c.name for c in self.client.get_collections().collections]
        if COLLECTION_NAME not in existing:
            self.client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
            )

    def _embed(self, text: str) -> list[float]:
        """Convert text to a vector using OpenAI embeddings."""
        response = self.openai.embeddings.create(
            input=text,
            model=EMBEDDING_MODEL,
        )
        return response.data[0].embedding

    def save(self, text: str, metadata: Optional[dict] = None) -> str:
        """
        Embed and upsert a memory into Qdrant.

        Args:
            text: The memory content to store.
            metadata: Optional key-value pairs attached to the memory (e.g. agent, date, tags).

        Returns:
            The UUID of the stored point.
        """
        point_id = str(uuid.uuid4())
        vector = self._embed(text)
        payload = {"text": text, **(metadata or {})}

        self.client.upsert(
            collection_name=COLLECTION_NAME,
            points=[PointStruct(id=point_id, vector=vector, payload=payload)],
        )
        return point_id

    def search(self, query: str, top_k: int = 5, agent: Optional[str] = None) -> list[dict]:
        """
        Semantic search over stored memories.

        Args:
            query: Natural language query.
            top_k: Number of results to return.
            agent: Optional filter to scope search to a specific agent's memories.

        Returns:
            List of matched memories with their text, score, and metadata.
        """
        vector = self._embed(query)

        query_filter = None
        if agent:
            from qdrant_client.models import Filter, FieldCondition, MatchValue
            query_filter = Filter(
                must=[FieldCondition(key="agent", match=MatchValue(value=agent))]
            )

        results = self.client.query_points(
            collection_name=COLLECTION_NAME,
            query=vector,
            limit=top_k,
            query_filter=query_filter,
            with_payload=True,
        )

        return [
            {
                "text": hit.payload.get("text", ""),
                "score": round(hit.score, 4),
                "metadata": {k: v for k, v in hit.payload.items() if k != "text"},
            }
            for hit in results.points
        ]

    def get_recent_ingested(self, limit: int = 10) -> list:
        """
        Return the most recently ingested file chunks (PDFs, text files).
        Used to ensure uploaded documents always appear in agent context.
        """
        from qdrant_client.models import Filter, FieldCondition, MatchAny

        results, _ = self.client.scroll(
            collection_name=COLLECTION_NAME,
            scroll_filter=Filter(
                must=[
                    FieldCondition(
                        key="type",
                        match=MatchAny(any=["ingested_pdf", "ingested_file", "ingested_text"]),
                    )
                ]
            ),
            limit=limit,
            with_payload=True,
            with_vectors=False,
        )

        return [
            {
                "text": point.payload.get("text", ""),
                "metadata": {k: v for k, v in point.payload.items() if k != "text"},
            }
            for point in results
        ]
