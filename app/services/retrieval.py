import math
from hashlib import sha256
from pathlib import Path

try:
    from sentence_transformers import SentenceTransformer
except Exception:  # pragma: no cover - optional heavy dep
    SentenceTransformer = None


def _tokenize(text: str) -> list[str]:
    return [t for t in text.lower().split() if t]


class HybridRetriever:
    def __init__(self, corpus: list[dict]):
        self.corpus = corpus
        self.encoder = None
        self.embeddings: list = []
        if SentenceTransformer:
            try:
                self.encoder = SentenceTransformer("all-MiniLM-L6-v2")
                texts = [c["text"] for c in corpus]
                self.embeddings = self.encoder.encode(texts, show_progress_bar=False)
            except Exception:
                self.encoder = None
                self.embeddings = []
        self._precompute_bm25()

    @staticmethod
    def load_from_path(path: Path) -> "HybridRetriever":
        docs: list[dict] = []
        for file in path.glob("*.txt"):
            text = file.read_text(encoding="utf-8")
            chunks = HybridRetriever._chunk_text(text, chunk_size=160)
            for idx, chunk in enumerate(chunks):
                docs.append({"id": f"{file.stem}-{idx}", "title": file.stem, "text": chunk})
        if not docs:
            docs = [
                {"id": "fallback-0", "title": "policy", "text": "Fallback policy document."},
            ]
        return HybridRetriever(docs)

    @staticmethod
    def _chunk_text(text: str, chunk_size: int) -> list[str]:
        tokens = _tokenize(text)
        if not tokens:
            return [""]
        chunks = []
        for i in range(0, len(tokens), chunk_size):
            chunk_tokens = tokens[i : i + chunk_size]
            chunks.append(" ".join(chunk_tokens))
        return chunks

    def _precompute_bm25(self) -> None:
        self.doc_tokens: list[list[str]] = []
        self.doc_lengths: list[int] = []
        self.df: dict[str, int] = {}
        for doc in self.corpus:
            tokens = _tokenize(doc["text"])
            self.doc_tokens.append(tokens)
            self.doc_lengths.append(len(tokens))
            for t in set(tokens):
                self.df[t] = self.df.get(t, 0) + 1
        avgdl = sum(self.doc_lengths) / max(len(self.doc_lengths), 1)
        self.avgdl = avgdl if avgdl > 0 else 1.0
        self.N = max(len(self.corpus), 1)

    def _bm25_scores(
        self, query: str, k1: float = 1.5, b: float = 0.75
    ) -> list[tuple[float, dict]]:
        q_tokens = _tokenize(query)
        scores: list[tuple[float, dict]] = []
        for idx, doc in enumerate(self.corpus):
            doc_len = self.doc_lengths[idx] or 1
            score = 0.0
            tf_counts: dict[str, int] = {}
            for t in self.doc_tokens[idx]:
                tf_counts[t] = tf_counts.get(t, 0) + 1
            for t in q_tokens:
                if t not in tf_counts:
                    continue
                df = self.df.get(t, 0)
                idf = math.log((self.N - df + 0.5) / (df + 0.5) + 1)
                tf = tf_counts[t]
                denom = tf + k1 * (1 - b + b * doc_len / self.avgdl)
                score += idf * ((tf * (k1 + 1)) / denom)
            scores.append((score, doc))
        return scores

    def _dense_scores(self, query: str) -> list[tuple[float, dict]]:
        if self.encoder is None or len(self.embeddings) == 0:
            return [(0.0, doc) for doc in self.corpus]
        query_vec = self.encoder.encode([query], show_progress_bar=False)[0]
        scores: list[tuple[float, dict]] = []
        for vec, doc in zip(self.embeddings, self.corpus, strict=False):
            dot = float((vec * query_vec).sum())
            norm = float((vec**2).sum()) ** 0.5 * float((query_vec**2).sum()) ** 0.5
            sim = dot / norm if norm else 0.0
            scores.append((sim, doc))
        return scores

    def search(self, query: str, k: int = 5) -> list[dict]:
        bm25 = self._bm25_scores(query)
        dense = self._dense_scores(query)
        combined: dict[str, tuple[float, dict]] = {}

        for score, doc in bm25:
            combined[doc["id"]] = (score, doc)

        for d_score, doc in dense:
            prev = combined.get(doc["id"], (0.0, doc))
            combined[doc["id"]] = (prev[0] + 0.6 * d_score, doc)

        ranked = sorted(combined.values(), key=lambda x: x[0], reverse=True)
        results = []
        seen_hashes = set()
        for score, doc in ranked:
            doc_hash = sha256(doc["text"].encode()).hexdigest()
            if doc_hash in seen_hashes:
                continue
            seen_hashes.add(doc_hash)
            doc_copy = dict(doc)
            doc_copy["score"] = round(score, 4)
            doc_copy["hash"] = doc_hash
            results.append(doc_copy)
            if len(results) >= k:
                break
        return results
