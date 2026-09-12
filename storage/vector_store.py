"""
Sovereign Gotham - Air-Gapped Hybrid Vector Store
Provides dense semantic retrieval with ChromaDB backing and sovereign local fallbacks.
"""

from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

try:
    import chromadb
    HAS_CHROMADB = True
except ImportError:
    HAS_CHROMADB = False


class SovereignVectorStore:
    """
    Air-gapped vector store.
    Uses ChromaDB if available; provides deterministic offline TF-IDF/Dense embeddings fallback.
    """

    def __init__(self, persist_directory: str = "storage/chroma_db", collection_name: str = "gotham_intel"):
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.use_chroma = HAS_CHROMADB
        self.chroma_client = None
        self.collection = None

        # Fallback in-memory store
        self.corpus: list[str] = []
        self.metadatas: list[dict[str, Any]] = []
        self.ids: list[str] = []
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words='english')
        self.matrix = None

        if self.use_chroma:
            try:
                self.chroma_client = chromadb.PersistentClient(path=self.persist_directory)
                self.collection = self.chroma_client.get_or_create_collection(
                    name=self.collection_name,
                    metadata={"hnsw:space": "cosine"}
                )
            except Exception:
                self.use_chroma = False

    def add_texts(self, texts: list[str], metadatas: list[dict[str, Any]], ids: list[str]) -> None:
        """Add text chunks with associated provenance metadata."""
        if not texts:
            return

        # Store in local in-memory fallback
        for t, m, i in zip(texts, metadatas, ids):
            if i not in self.ids:
                self.ids.append(i)
                self.corpus.append(t)
                self.metadatas.append(m)

        if self.corpus:
            self.matrix = self.vectorizer.fit_transform(self.corpus)

        # Store in ChromaDB if active
        if self.use_chroma and self.collection:
            try:
                # Sanitize metadata for ChromaDB (must be str/int/float/bool)
                clean_metas = []
                for meta in metadatas:
                    cm = {}
                    for k, v in meta.items():
                        if isinstance(v, (str, int, float, bool)):
                            cm[k] = v
                        else:
                            cm[k] = str(v)
                    clean_metas.append(cm)

                self.collection.upsert(
                    documents=texts,
                    metadatas=clean_metas,
                    ids=ids
                )
            except Exception as e:
                print(f"[VectorStore Warning] Chroma upsert failed, relying on local fallback: {e}")

    def similarity_search(
        self,
        query: str,
        top_k: int = 5,
        where: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Perform cosine similarity search over ingested intelligence with optional metadata filtering."""
        results = []

        if self.use_chroma and self.collection:
            try:
                query_kwargs: dict[str, Any] = {
                    "query_texts": [query],
                    "n_results": min(top_k, self.collection.count() or top_k),
                }
                if where:
                    query_kwargs["where"] = where

                q_res = self.collection.query(**query_kwargs)
                if q_res and q_res.get("documents") and q_res["documents"][0]:

                    for idx, doc in enumerate(q_res["documents"][0]):
                        results.append({
                            "id": q_res["ids"][0][idx],
                            "text": doc,
                            "metadata": q_res["metadatas"][0][idx] if q_res["metadatas"] else {},
                            "distance": q_res["distances"][0][idx] if q_res.get("distances") else 0.0
                        })
                    return results
            except Exception as e:
                print(f"[VectorStore Warning] Chroma query failed, falling back to sovereign index: {e}")

        # Fallback deterministic TF-IDF search
        if not self.corpus or self.matrix is None:
            return []

        q_vec = self.vectorizer.transform([query])
        sims = cosine_similarity(q_vec, self.matrix).flatten()
        ranked_indices = np.argsort(sims)[::-1][:top_k]

        for r_idx in ranked_indices:
            score = float(sims[r_idx])
            if score > 0.01:
                results.append({
                    "id": self.ids[r_idx],
                    "text": self.corpus[r_idx],
                    "metadata": self.metadatas[r_idx],
                    "score": score
                })

        return results
