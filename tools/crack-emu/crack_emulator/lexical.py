"""Character n-gram BM25.

Lexical, not semantic: no embeddings, no external service. Used only when
`memory.recalled_selection: lexical` is chosen, since Crack itself appears to
match on text rather than vectors.
"""
from __future__ import annotations

import math
import unicodedata
from collections import Counter


def ngrams(text: str, n: int = 3) -> list[str]:
    t = unicodedata.normalize("NFKC", text).casefold()
    t = "".join(ch if ch.isalnum() else " " for ch in t)
    toks: list[str] = []
    for word in t.split():
        if len(word) <= n:
            toks.append(word)
        else:
            toks.extend(word[i:i + n] for i in range(len(word) - n + 1))
    return toks


class BM25:
    def __init__(self, docs: list[str], k1: float = 1.5, b: float = 0.75, n: int = 3):
        self.k1, self.b, self.n = k1, b, n
        self.docs = docs
        self.toks = [ngrams(d, n) for d in docs]
        self.lens = [len(t) for t in self.toks]
        self.avglen = (sum(self.lens) / len(self.lens)) if self.lens else 0.0
        self.df: Counter[str] = Counter()
        for t in self.toks:
            self.df.update(set(t))
        self.N = len(docs)

    def _idf(self, term: str) -> float:
        df = self.df.get(term, 0)
        return math.log(1 + (self.N - df + 0.5) / (df + 0.5))

    def search(self, query: str, top_k: int = 3) -> list[tuple[int, float]]:
        if not self.N:
            return []
        q = ngrams(query, self.n)
        scores = []
        for i, toks in enumerate(self.toks):
            tf = Counter(toks)
            s = 0.0
            for term in q:
                f = tf.get(term, 0)
                if not f:
                    continue
                denom = f + self.k1 * (1 - self.b + self.b * self.lens[i] / (self.avglen or 1))
                s += self._idf(term) * f * (self.k1 + 1) / denom
            scores.append((i, s))
        scores.sort(key=lambda x: -x[1])
        return [(i, s) for i, s in scores[:top_k] if s > 0]
