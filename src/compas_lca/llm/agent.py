from __future__ import annotations

import time

from dataclasses import dataclass

from typing import Any
from typing import Optional
from typing import Dict

from pydantic_ai import Agent as PydanticAgent
from pydantic_ai.usage import RunUsage

from .context import Context

@dataclass
class RunMetadata:
    started_at: float
    ended_at: float
    duration_s: float
    model: Optional[str]
    usage: Optional[RunUsage] = None
    currency: str = "USD"
    input_cost: Optional[float] = None
    output_cost: Optional[float] = None
    total_cost: Optional[float] = None


class CompasAgent:

    """
    Serializable wrapper around PydanticAI Agent class configurations.
    Combine with a Context per run to create/execute underlying Pydantic Agent class.
    """

    def __init__(
        self,
        *,
        model: Optional[str] = None,
        retries: int = 1,
        model_settings: Optional[Dict[str, Any]] = None,
        pricing_table: Optional[Dict[str, Dict[str, float]]] = None,
        currency: str = "USD",
        context: Optional[Context] = None,
    ):
        self._model = model
        self._retries = retries
        self._model_settings = dict(model_settings) if isinstance(model_settings, dict) else None
        self._pricing_table = pricing_table or {}   # {"provider:model": {"in_per_1k": ..., "out_per_1k": ...}}
        self._currency = currency
        self._context: Optional[Context] = context
        self._last_result: Any = None
        self._last_metadata: Optional[RunMetadata] = None
        self._run_history: list[RunMetadata] = []

    @property
    def __data__(self) -> dict:
        return {
            "model": self._model,
            "retries": self._retries,
            "model_settings": self._model_settings,
            "pricing_table": self._pricing_table,
            "currency": self._currency,
        }

    @classmethod
    def __from_data__(cls, data: dict) -> "CompasAgent":
        return cls(
            model=data.get("model"),
            retries=data.get("retries", 1),
            model_settings=data.get("model_settings"),
            pricing_table=data.get("pricing_table") or {},
            currency=data.get("currency", "USD"),
        )

    def set_pricing(self, model: str, in_per_1k: float, out_per_1k: float, *, currency: Optional[str] = None):
        self._pricing_table.setdefault(model, {})
        self._pricing_table[model]["in_per_1k"] = float(in_per_1k)
        self._pricing_table[model]["out_per_1k"] = float(out_per_1k)
        if currency:
            self._currency = currency
        return self

    def _estimate_cost(self, usage: Optional[RunUsage]) -> Dict[str, Optional[float]]:
        if not usage or not self._model or self._model not in self._pricing_table:
            return {"input_cost": None, "output_cost": None, "total_cost": None}
        p = self._pricing_table[self._model]
        ic = (usage.input_tokens / 1000.0) * float(p.get("in_per_1k", 0.0))
        oc = (usage.output_tokens / 1000.0) * float(p.get("out_per_1k", 0.0))
        return {"input_cost": ic, "output_cost": oc, "total_cost": ic + oc}

    def _build_agent(self, context_input: Context) -> PydanticAgent:
        if context_input is None:
            raise ValueError("A Context is required. Pass one to the run/run_sync method.")
        agent = PydanticAgent(
            self._model,
            retries=self._retries,
            model_settings=self._model_settings,
            **context_input.to_agent_kwargs(),
        )
        if context_input.tools:
            for tool in context_input.tools:
                if hasattr(agent, "tool") and callable(getattr(agent, "tool")):
                    agent.tool(tool)            
                elif hasattr(agent, "add_tool"):
                    agent.add_tool(tool)        
                else:
                    pass
        return agent

    def bind(self, context_input: Context) -> "CompasAgent":
        self._context = context_input
        return self

    def run_sync(self, *args, context_input: Optional[Context] = None, **kwargs):
        ctx = context_input or self._context
        agent = self._build_agent(ctx)
        t0 = time.perf_counter()
        result = agent.run_sync(*args, **kwargs)
        t1 = time.perf_counter()
        usage = getattr(result, "usage", None)
        if callable(usage):
            usage = usage()
        costs = self._estimate_cost(usage)
        meta = RunMetadata(
            started_at=t0, ended_at=t1, duration_s=t1 - t0,
            model=self._model, usage=usage, currency=self._currency, **costs
        )
        self._last_metadata = meta
        self._run_history.append(meta)
        self._last_result = result
        return result

    async def run(self, *args, context_input: Optional[Context] = None, **kwargs):
        ctx = context_input or self._context
        agent = self._build_agent(ctx)
        t0 = time.perf_counter()
        result = await agent.run(*args, **kwargs)
        t1 = time.perf_counter()
        usage = getattr(result, "usage", None)
        if callable(usage):
            usage = usage()
        costs = self._estimate_cost(usage)
        meta = RunMetadata(
            started_at=t0, ended_at=t1, duration_s=t1 - t0,
            model=self._model, usage=usage, currency=self._currency, **costs
        )
        self._last_metadata = meta
        self._run_history.append(meta)
        self._last_result = result
        return result

    def run_stream(self, *args, context_input: Optional[Context] = None, **kwargs):
        ctx = context_input or self._context
        agent = self._build_agent(ctx)
        return agent.run_stream(*args, **kwargs)

    @property
    def last_metadata(self) -> Optional[RunMetadata]:
        return self._last_metadata

    @property
    def last_result(self) -> Any:
        return self._last_result

    @property
    def run_history(self) -> list[RunMetadata]:
        return list(self._run_history)
