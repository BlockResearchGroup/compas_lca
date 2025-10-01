from dataclasses import dataclass

import time

from typing import Any
from typing import Optional

from pydantic_ai import Agent as PydanticAgent
from pydantic_ai.usage import RunUsage

from .context import Context

from .agent_settings import AgentSettings

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

@dataclass
class Run:
    result: Any
    metadata: RunMetadata

class CompasAgent:
    def __init__(self, *, settings: AgentSettings, context: Context):
        self._settings = settings
        self._context = context
        self._last_run: Optional[Run] = None
        self._history_runs: list[Run] = []
        self._pydantic_agent = self._make_agent(context)

    # build agent once
    def _make_agent(self, ctx: Context) -> PydanticAgent:
        agent = PydanticAgent(
            self._settings.model,
            retries=self._settings.retries,
            model_settings=self._settings.model_settings or None,
            **ctx.to_agent_kwargs(),
        )
        for tool in ctx.tools or ():
            if hasattr(agent, "tool"):
                agent.tool(tool)
        return agent

    # single run endpoint to user
    def execute_run(self, *args, as_async: bool = False, stream: bool = False, **kwargs):
        if as_async and stream:
            raise NotImplementedError("Streaming+async not supported by this wrapper.")
        if stream:
            return self._run_stream(*args, **kwargs)
        if as_async:
            return self._run_async(*args, **kwargs)
        return self._run_sync(*args, **kwargs)

    # internals
    def _record_run(self, started_at: float, result: Any) -> Run:
        ended_at = time.perf_counter()

        usage = getattr(result, "usage", None)
        if callable(usage):
            usage = usage()
        if usage is not None:
            in_tok = getattr(usage, "input_tokens", None) or 0
            out_tok = getattr(usage, "output_tokens", None) or 0
            costs = self._settings.estimate_cost(usage_in_tokens=(in_tok, out_tok))
        else:
            costs = {"input_cost": None, "output_cost": None, "total_cost": None}

        meta = RunMetadata(
            started_at=started_at,
            ended_at=ended_at,
            duration_s=ended_at - started_at,
            model=self._settings.model,
            usage=usage,
            currency=self._settings.currency,
            **costs,
        )
        run = Run(result=result, metadata=meta)
        self._last_run = run
        self._history_runs.append(run)
        return run

    def _run_sync(self, *args, **kwargs) -> Run:
        t0 = time.perf_counter()
        result = self._pydantic_agent.run_sync(*args, **kwargs)
        return self._record_run(t0, result)

    async def _run_async(self, *args, **kwargs) -> Run:
        t0 = time.perf_counter()
        result = await self._pydantic_agent.run(*args, **kwargs)
        return self._record_run(t0, result)

    def _run_stream(self, *args, **kwargs):
        t0 = time.perf_counter()
        gen = self._pydantic_agent.run_stream(*args, **kwargs)
        last = None
        try:
            for chunk in gen:
                last = chunk
                yield chunk
        finally:
            self._record_run(t0, last if last is not None else getattr(gen, "result", None))

    # properties
    @property
    def last_run(self) -> Optional[Run]:
        return self._last_run

    @property
    def history_runs(self) -> list[Run]:
        return list(self._history_runs)