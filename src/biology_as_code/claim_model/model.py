"""
The learned component: predict a claim's evidence grade from its language.

Scope, stated narrowly on purpose. This model predicts ONE thing — the evidence
grade (A/B/C/D) a claim would be assigned — from the claim's surface text and a
small number of graph features. It does **not** predict the verdict. The verdict
is computed by :mod:`biology_as_code.claim_model.court` from the constitution,
so a mis-prediction here can weaken a verdict but can never manufacture one.

That split is the whole design. A model that emitted "Confirmed" directly would
be a model that could fabricate an adjudication, which is the failure the
register exists to prevent.

Implementation is a multinomial logistic regression over hashed word and
character n-grams, in pure Python. No third-party dependency, deterministic
given a seed, and small enough to train in seconds on the 1,228 labelled claims
in the corpus.

    from biology_as_code.claim_model import EvidenceGradeModel
    m = EvidenceGradeModel.train_from_graph(g)
    m.predict("Blunts postprandial glucose response")   # ('B', {...})
"""

from __future__ import annotations

import json
import math
import random
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

GRADES = ("A", "B", "C", "D")
_WORD = re.compile(r"[a-z0-9']+")


# ---------------------------------------------------------------- features

def featurize(text: str, extra: dict[str, Any] | None = None) -> dict[str, float]:
    """
    Hashed bag of words, word bigrams, and 4-char shingles, plus graph features.

    Character shingles matter here because the corpus is full of morphological
    near-misses ("blunts" / "blunting", "lowers" / "lowering") and the training
    set is small.
    """
    t = (text or "").lower()
    feats: dict[str, float] = {"__bias__": 1.0}

    words = _WORD.findall(t)
    for w in words:
        feats[f"w:{w}"] = feats.get(f"w:{w}", 0.0) + 1.0
    for a, b in zip(words, words[1:]):
        k = f"b:{a}_{b}"
        feats[k] = feats.get(k, 0.0) + 1.0
    squashed = re.sub(r"\s+", " ", t)
    for i in range(len(squashed) - 3):
        k = f"c:{squashed[i:i + 4]}"
        feats[k] = feats.get(k, 0.0) + 1.0

    feats["len:words"] = min(len(words), 60) / 60.0

    for key, val in (extra or {}).items():
        if isinstance(val, bool):
            feats[f"g:{key}"] = 1.0 if val else 0.0
        elif isinstance(val, (int, float)):
            feats[f"g:{key}"] = float(val)
        elif val is not None:
            feats[f"g:{key}={val}"] = 1.0

    # L2 normalise so long statements do not dominate
    norm = math.sqrt(sum(v * v for v in feats.values())) or 1.0
    return {k: v / norm for k, v in feats.items()}


# ---------------------------------------------------------------- the model

@dataclass
class EvidenceGradeModel:
    """Multinomial logistic regression over sparse text features."""

    weights: dict[str, dict[str, float]]
    classes: tuple[str, ...] = GRADES
    trained_on: int = 0
    metrics: dict[str, Any] | None = None

    # -------------------------------------------------------- prediction

    def scores(self, text: str, extra: dict[str, Any] | None = None) -> dict[str, float]:
        feats = featurize(text, extra)
        raw = {
            c: sum(w * self.weights.get(c, {}).get(f, 0.0) for f, w in feats.items())
            for c in self.classes
        }
        top = max(raw.values())
        exp = {c: math.exp(v - top) for c, v in raw.items()}
        total = sum(exp.values()) or 1.0
        return {c: v / total for c, v in exp.items()}

    def predict(
        self, text: str, extra: dict[str, Any] | None = None
    ) -> tuple[str, dict[str, float]]:
        probs = self.scores(text, extra)
        return max(probs, key=probs.__getitem__), probs

    def confidence(self, text: str, extra: dict[str, Any] | None = None) -> float:
        """Margin between the top two classes — how sure, not just which."""
        p = sorted(self.scores(text, extra).values(), reverse=True)
        return p[0] - p[1] if len(p) > 1 else p[0]

    # -------------------------------------------------------- training

    @classmethod
    def train(
        cls,
        samples: list[tuple[str, str, dict[str, Any]]],
        *,
        epochs: int = 12,
        lr: float = 0.5,
        l2: float = 1e-4,
        seed: int = 0,
        holdout: float = 0.2,
    ) -> EvidenceGradeModel:
        """
        Fit on ``(text, grade, extra)`` triples.

        A deterministic seed and a fixed shuffle make the fit reproducible,
        which the repo requires of anything that ships a number.
        """
        rng = random.Random(seed)
        data = [s for s in samples if s[1] in GRADES]
        rng.shuffle(data)

        cut = int(len(data) * (1 - holdout))
        train, test = data[:cut], data[cut:]

        weights: dict[str, dict[str, float]] = {c: {} for c in GRADES}
        cached = [(featurize(t, e), g) for t, g, e in train]

        for epoch in range(epochs):
            rng.shuffle(cached)
            step = lr / (1 + epoch)
            for feats, gold in cached:
                raw = {
                    c: sum(w * weights[c].get(f, 0.0) for f, w in feats.items())
                    for c in GRADES
                }
                top = max(raw.values())
                exp = {c: math.exp(v - top) for c, v in raw.items()}
                total = sum(exp.values()) or 1.0
                for c in GRADES:
                    err = (exp[c] / total) - (1.0 if c == gold else 0.0)
                    if abs(err) < 1e-9:
                        continue
                    wc = weights[c]
                    for f, v in feats.items():
                        wc[f] = wc.get(f, 0.0) * (1 - step * l2) - step * err * v

        model = cls(weights=weights, trained_on=len(train))
        model.metrics = model.evaluate(test) if test else None
        return model

    @classmethod
    def train_from_graph(cls, graph: Any, **kw: Any) -> EvidenceGradeModel:
        """Pull labelled claims straight out of the graph and fit."""
        return cls.train(samples_from_graph(graph), **kw)

    # -------------------------------------------------------- evaluation

    def evaluate(self, samples: list[tuple[str, str, dict[str, Any]]]) -> dict[str, Any]:
        if not samples:
            return {"n": 0}
        correct = 0
        confusion: dict[str, dict[str, int]] = {c: dict.fromkeys(GRADES, 0) for c in GRADES}
        for text, gold, extra in samples:
            pred, _ = self.predict(text, extra)
            confusion[gold][pred] += 1
            correct += pred == gold
        n = len(samples)
        majority = max(
            sum(1 for _, g, _ in samples if g == c) for c in GRADES
        )
        per_class = {}
        for c in GRADES:
            tp = confusion[c][c]
            fp = sum(confusion[o][c] for o in GRADES if o != c)
            fn = sum(confusion[c][o] for o in GRADES if o != c)
            prec = tp / (tp + fp) if tp + fp else 0.0
            rec = tp / (tp + fn) if tp + fn else 0.0
            f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
            per_class[c] = {"precision": round(prec, 3), "recall": round(rec, 3),
                            "f1": round(f1, 3), "support": tp + fn}
        return {
            "n": n,
            "accuracy": round(correct / n, 4),
            "majority_baseline": round(majority / n, 4),
            "per_class": per_class,
            "confusion": confusion,
        }

    # -------------------------------------------------------- persistence

    def save(self, path: str | Path, *, top_k: int = 4000) -> None:
        """Serialise, keeping only the highest-magnitude weights per class."""
        pruned = {
            c: dict(sorted(w.items(), key=lambda kv: -abs(kv[1]))[:top_k])
            for c, w in self.weights.items()
        }
        Path(path).write_text(
            json.dumps(
                {"classes": list(self.classes), "trained_on": self.trained_on,
                 "metrics": self.metrics, "weights": pruned},
                sort_keys=True,
            ),
            encoding="utf-8",
        )

    @classmethod
    def load(cls, path: str | Path) -> EvidenceGradeModel:
        d = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(
            weights=d["weights"],
            classes=tuple(d.get("classes", GRADES)),
            trained_on=d.get("trained_on", 0),
            metrics=d.get("metrics"),
        )

    def top_features(self, grade: str, n: int = 15) -> list[tuple[str, float]]:
        """What the model actually learned — for inspection, not decoration."""
        return sorted(self.weights.get(grade, {}).items(), key=lambda kv: -kv[1])[:n]


# ---------------------------------------------------------------- data

def samples_from_graph(graph: Any) -> list[tuple[str, str, dict[str, Any]]]:
    """
    Labelled claims from the graph: statement text, evidence grade, graph features.

    Graph features are deliberately thin — how many bioactives are credited, and
    the food's NOVA class. Anything richer risks the model learning the label
    from the food's identity rather than from the claim's language.
    """
    out: list[tuple[str, str, dict[str, Any]]] = []
    for node in graph.nodes("Claim"):
        grade = node.props.get("evidence_grade")
        if grade not in GRADES:
            continue
        drivers = node.props.get("drivers") or []
        extra: dict[str, Any] = {
            "n_drivers": min(len(drivers), 5) / 5.0,
            "outcome": node.props.get("outcome"),
        }
        if food_id := node.props.get("food"):
            if food := graph.get_node(f"food:{food_id}"):
                extra["nova"] = food.props.get("nova_class")
                extra["group"] = food.props.get("group")
        out.append((node.name, grade, extra))
    return out


__all__ = ["EvidenceGradeModel", "featurize", "samples_from_graph", "GRADES"]
