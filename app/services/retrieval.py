import math
from pathlib import Path
from typing import Dict, List, Tuple
from hashlib import sha256

try:
    from sentence_transformers import SentenceTransformer
except Exception:  # pragma: no cover - optional heavy dep
    SentenceTransformer = None


class HybridRetriever:
    def __init__(self, corpus: List[Dict]):
        self.corpus = corpus
        self.encoder = None
        if SentenceTransformer:
            try:
                self.encoder = SentenceTransformer("all-MiniLM-L6-v2")
                texts = [c["text"] for c in corpus]
                self.embeddings = self.encoder.encode(texts, show_progress_bar=False)
            except Exception:
                self.encoder = None
                self.embeddings = []
        else:
            self.embeddings = []

    @staticmethod
    def load_from_path(path: Path) -> "HybridRetriever":
        docs: List[Dict] = []
        for file in path.glob("*.txt"):
            text = file.read_text(encoding="utf-8")
            docs.append({"id": file.stem, "title": file.stem, "text": text})
        if not docs:
            docs = [
                {"id": "fallback", "title": "policy", "text": "Fallback policy document."},
            ]
        return HybridRetriever(docs)

    def _bm25_scores(self, query: str) -> List[Tuple[float, Dict]]:
        tokens = query.lower().split()
        scores = []
        for doc in self.corpus:
            text_tokens = doc["text"].lower().split()
            score = 0.0
            for t in tokens:
                tf = text_tokens.count(t)
                if tf == 0:
                    continue
                score += (tf / len(text_tokens)) * math.log(1 + len(self.corpus))
            scores.append((score, doc))
        return scores

    def _dense_scores(self, query: str) -> List[Tuple[float, Dict]]:
        if self.encoder is None or len(self.embeddings) == 0:
            return [(0.0, doc) for doc in self.corpus]
        query_vec = self.encoder.encode([query], show_progress_bar=False)[0]
        scores: List[Tuple[float, Dict]] = []
        for vec, doc in zip(self.embeddings, self.corpus):
            # cosine similarity
            dot = float((vec * query_vec).sum())
            norm = float((vec**2).sum()) ** 0.5 * float((query_vec**2).sum()) ** 0.5
            sim = dot / norm if norm else 0.0
            scores.append((sim, doc))
        return scores

    def search(self, query: str, k: int = 3) -> List[Dict]:
        bm25 = self._bm25_scores(query)
        dense = self._dense_scores(query)
        combined: Dict[str, Tuple[float, Dict]] = {}
        for score, doc in bm25 + dense:
            existing = combined.get(doc["id"], (0.0, doc))
            combined[doc["id"]] = (existing[0] + score, doc)
        ranked = sorted(combined.values(), key=lambda x: x[0], reverse=True)
        results = []
        for score, doc in ranked[:k]:
            doc_copy = dict(doc)
            doc_copy["score"] = score
            doc_copy["hash"] = sha256(doc["text"].encode()).hexdigest()
            results.append(doc_copy)
        return results
