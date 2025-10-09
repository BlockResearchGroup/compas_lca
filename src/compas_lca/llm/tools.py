from dataclasses import dataclass

import csv

import re

from pathlib import Path

from typing import Dict
from typing import Tuple
from typing import Iterable
from typing import Optional

from pydantic import BaseModel
from pydantic_ai import RunContext

# ---------- REBAR TOOL ----------

# input csv rebar tool path
REBAR_RATIO_CSV = (Path(__file__).resolve().parent / "data" / "tools" / "rebar_ratios.csv")

class RebarRatio(BaseModel):
    """Output model"""
    component: str  # matched canonical key
    min_ratio: float  # volume fraction m3/m3
    max_ratio: float  # volume fraction m3/m3
    basis: str = "volume_fraction_m3_per_m3"

@dataclass
class RebarTable:
    """Holds normalized lookup from component -> (min, max)."""
    ratios: Dict[str, Tuple[float, float]]

    @staticmethod
    def _norm(s: str) -> str:
        # normalize weird strings in csv
        s = s.strip().lower()
        s = re.sub(r"[\s\-_/]+", " ", s)
        s = re.sub(r"\s+", " ", s)
        return s

    @classmethod
    def from_csv(cls, path: Path | str = REBAR_RATIO_CSV) -> "RebarTable":
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Rebar ratios CSV not found: {path}")
        ratios: Dict[str, Tuple[float, float]] = {}
        with path.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            # Expect columns:
            # Building Component, Min. Ratio of reinforcement in m3/m3, Max. Ratio of reinforcement in m3/m3
            for row in reader:
                name = str(row["Building Component"]).strip()
                min_v = float(row["Min. Ratio of reinforcement in m3/m3"])
                max_v = float(row["Max. Ratio of reinforcement in m3/m3"])
                ratios[cls._norm(name)] = (min_v, max_v)
        return cls(ratios=ratios)

    def keys(self) -> Iterable[str]:
        return self.ratios.keys()

    def best_match(self, query: str) -> Optional[Tuple[str, Tuple[float, float]]]:
        """
        Try exact normalized match; otherwise try a simple substring containment
        (e.g., 'retaining wall' -> 'retaining walls').
        """
        q = self._norm(query)
        if q in self.ratios:
            return q, self.ratios[q]
        tokens = q.split()
        for k in self.ratios:
            if all(t in k for t in tokens):
                return k, self.ratios[k]
        return None

def rebar_ratio_lookup(ctx: RunContext[RebarTable], component: str) -> RebarRatio:
    """
    Tool: given a building component description, return min/max rebar ratios (m3/m3).
    Case/spacing/punctuation-insensitive; supports loose matches.
    """
    match = ctx.deps.best_match(component)
    if not match:
        raise ValueError(
            f"Unknown component '{component}'. "
            f"Try one of: {', '.join(sorted(ctx.deps.keys()))}"
        )
    key, (mn, mx) = match
    return RebarRatio(component=key, min_ratio=mn, max_ratio=mx)
