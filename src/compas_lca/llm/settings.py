from typing import Any
from typing import Dict
from typing import Optional
from typing import Tuple

from pydantic import BaseModel
from pydantic import Field
from pydantic import field_validator

class AgentSettings(BaseModel):
    model: str
    retries: int = 1
    model_settings: Dict[str, Any] = Field(default_factory=dict)
    pricing_table: Dict[str, Dict[str, float]] = Field(default_factory=dict)
    currency: str = "USD"

    def with_pricing(
        self,
        model: str,
        in_per_1k: float,
        out_per_1k: float,
        *,
        currency: Optional[str] = None,
    ) -> "AgentSettings":
        tbl = dict(self.pricing_table)
        tbl.setdefault(model, {})
        tbl[model]["in_per_1k"] = float(in_per_1k)
        tbl[model]["out_per_1k"] = float(out_per_1k)
        return self.model_copy(update={
            "pricing_table": tbl,
            "currency": currency or self.currency,
        })

    def estimate_cost(self, *, usage_in_tokens: Tuple[int, int]) -> Dict[str, Optional[float]]:
        in_tok, out_tok = usage_in_tokens
        prices = self.pricing_table.get(self.model)
        if not prices:
            return {"input_cost": None, "output_cost": None, "total_cost": None}
        ic = (in_tok / 1000.0) * prices.get("in_per_1k", 0.0)
        oc = (out_tok / 1000.0) * prices.get("out_per_1k", 0.0)
        return {"input_cost": ic, "output_cost": oc, "total_cost": ic + oc}

    def with_model_settings(self, **updates: Any) -> "AgentSettings":
        ms = {**self.model_settings, **updates}
        return self.model_copy(update={"model_settings": ms})

    @field_validator("retries")
    @classmethod
    def _non_negative_retries(cls, v: int) -> int:
        if v < 0:
            raise ValueError("retries must be >= 0")
        return v

    @field_validator("pricing_table")
    @classmethod
    def _validate_pricing_table(cls, v: Dict[str, Dict[str, float]]) -> Dict[str, Dict[str, float]]:
        for mdl, prices in v.items():
            for k in ("in_per_1k", "out_per_1k"):
                p = float(prices.get(k, 0.0))
                if p < 0:
                    raise ValueError(f"pricing_table[{mdl!r}][{k}] must be >= 0")
                prices[k] = p
        return v
