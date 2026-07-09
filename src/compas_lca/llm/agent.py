import yaml

import time

from dataclasses import dataclass

from pathlib import Path

from typing import Any
from typing import Optional
from typing import Self

from pydantic import ValidationError

from pydantic_ai import Agent as PydanticAgent
from pydantic_ai.usage import RunUsage

from .context import Context

from .settings import AgentSettings

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

    def to_dict(self) -> dict:
        """Convert metadata (including usage) to a plain serializable dict."""
        usage_dict = None
        if self.usage is not None:
            usage_dict = {
                "input_tokens": getattr(self.usage, "input_tokens", None),
                "output_tokens": getattr(self.usage, "output_tokens", None),
                "total_tokens": getattr(self.usage, "total_tokens", None),
            }

        return {
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "duration_s": self.duration_s,
            "model": self.model,
            "currency": self.currency,
            "usage": usage_dict,
            "costs": {
                "input_cost": self.input_cost,
                "output_cost": self.output_cost,
                "total_cost": self.total_cost,
            },
        }

    def to_json(self, *, indent: int = 2, ensure_ascii: bool = False) -> str:
        """Return a JSON string representation of the metadata."""
        import json
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=ensure_ascii)
    
    def summary(self) -> dict:
        """
        Flat summary used by downstream aggregation/merging.
        Keep this EXACT schema stable because extract_matching_core aggregates it.
        """
        usage = self.usage
        input_tokens = getattr(usage, "input_tokens", None) if usage else None
        output_tokens = getattr(usage, "output_tokens", None) if usage else None
        total_cost = self.total_cost

        return {
            "model": self.model,
            "duration_s": self.duration_s,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "currency": self.currency,
            "total_cost": total_cost,
        }

@dataclass
class Run:
    result: Any
    metadata: RunMetadata

    def save_metadata(self, path: str | Path) -> Path:
        """Write metadata to a JSON file."""
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(self.metadata.to_json(), encoding="utf-8")
        return p

class BaseAgent:
    """
    High-level wrapper around `pydantic_ai.Agent` that centralizes
    configuration, execution, usage tracking, and cost estimation for
    model-agnostic LLM-based extraction and reasoning workflows.
    
    ----------------------------------------------------------------------
    Parameters (constructor)
    ----------------------------------------------------------------------
    settings : AgentSettings
        Model name, retry settings, cost parameters, and model-specific
        configuration for the underlying LLM.
    context : Context
        Provides runtime information such as tools, system prompts,
        environment settings, or any additional information required by
        the agent during execution.    

    ----------------------------------------------------------------------
    Core Responsibilities
    ----------------------------------------------------------------------
    1. **Configuration Management**
       - Loads YAML configuration files and validates them against the
         `AgentSettings` model.
       - Constructs the underlying `pydantic_ai.Agent` using model,
         retry settings, and model-specific parameters.

    2. **Context Integration**
       - Injects runtime context (e.g., tools, system instructions,
         metadata) into the agent using `Context.to_pydantic_agent_kwargs()`.
       - Registers any tool functions declared inside the context.

    3. **Execution Wrappers**
       - `execute_run()` dispatches to:
           - `_run_sync()`   → synchronous execution
           - `_run_async()`  → asynchronous execution (awaitable)
           - `_run_stream()` → streaming token-by-token output
       - Provides a unified interface for these modes.

    4. **Usage Tracking and Cost Estimation**
       - Records timing, token usage, and cost for every run.
       - Wraps results in a `Run` object containing:
           - result payload
           - metadata: timestamps, token usage, model name, cost estimates

    5. **History Management**
       - Stores the most recent run (`last_run`)
       - Maintains a log of all executed runs (`history_runs`)

    ----------------------------------------------------------------------
    Typical Usage
    ----------------------------------------------------------------------
    >>> agent = BaseAgent.from_config(context=my_context)
    >>> run = agent.execute_run({"raw_input": data})
    >>> print(run.result)
    >>> print(run.metadata.total_cost)
    """
    def __init__(self, *, settings: AgentSettings, context: Context):
        self._settings = settings
        self._context = context
        self._last_run: Optional[Run] = None
        self._history_runs: list[Run] = []
        self._pydantic_agent = self._create_pydantic_agent(context)

    def _create_pydantic_agent(self, ctx: Context) -> PydanticAgent:
        agent = PydanticAgent(
            self._settings.model,
            retries=self._settings.retries,
            model_settings=self._settings.model_settings or None,
            **ctx.to_pydantic_agent_kwargs(),
        )
        for tool in ctx.tools or ():
            if hasattr(agent, "tool"):
                agent.tool(tool)
        return agent

    @classmethod
    def from_config(cls, config_path: str | Path = "config.yaml", *, context: Context) -> Self:
        """
        The YAML file must map 1-to-1 to the `AgentSettings` model.
        By default, this method looks for a `config.yaml` in the current
        working directory.

        Args:
            config_path: Path to the YAML configuration file.
            context:     A Context object providing runtime information.

        Returns:
            A fully-initialized `BaseAgent` (or subclass) instance.
        """
        try:
            data = yaml.safe_load(Path(config_path).read_text(encoding="utf-8")) or {}
            settings = AgentSettings.model_validate(data)
        except FileNotFoundError as e:
            raise FileNotFoundError(f"config.yaml file not found") from e
        except ValidationError as e:
            raise ValueError(f"Invalid config.yaml: {e}") from e
        return cls(settings=settings, context=context)

    def execute_run(self, *args, as_async: bool = False, stream: bool = False, **kwargs):
        """
        Execute the agent on a given input and record usage metadata.

        Args:
            *args, **kwargs:  Arguments forwarded to the underlying Pydantic agent.
            as_async:         If True, run asynchronously and return an awaitable.
            stream:           If True, yield streaming output chunks as they arrive.

        Returns:
            A `Run` object for sync/async modes, or a generator for streaming mode.
        """
        if as_async and stream:
            raise NotImplementedError("Streaming+async not supported by this wrapper.")
        if stream:
            return self._run_stream(*args, **kwargs)
        if as_async:
            return self._run_async(*args, **kwargs)
        return self._run_sync(*args, **kwargs)

    # Internals
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