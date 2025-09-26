from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from dataclasses import replace

from typing import Any
from typing import Optional
from typing import Sequence
from typing import Dict
from typing import Type
from typing import Callable
from typing import Iterable

@dataclass
class Context:

    """
    Context for any single agent/run:
    - prompts (instructions/system_prompt)
    - data schema (output_type)
    - dependency injection (deps_type)
    - optional tools and raw_data payloads
    - optional ephemeral name
    """

    instructions: Optional[str] = None
    system_prompt: Sequence[str] = field(default_factory=tuple)
    output_type: Optional[Type] = str
    deps_type: Optional[Type] = None
    name: Optional[str] = None
    tools: Optional[Iterable[Callable]] = None

    @property
    def __data__(self) -> dict:
        return {
            "instructions": self.instructions,
            "system_prompt": list(self.system_prompt),
            "name": self.name,
            "has_output_type": self.output_type is not None,
            "has_deps_type": self.deps_type is not None,
            "has_tools": bool(self.tools)
        }

    @classmethod
    def __from_data__(cls, data: dict) -> "Context":
        return cls(
            instructions=data.get("instructions"),
            system_prompt=tuple(data.get("system_prompt") or ()),
            name=data.get("name"),
            output_type=data.get("output_type", str),
            deps_type=data.get("deps_type"),
            tools=tuple(data.get("tools") or ()),
        )

    def to_agent_kwargs(self) -> Dict[str, Any]:
        return dict(
            output_type=self.output_type or str,
            instructions=self.instructions,
            system_prompt=tuple(self.system_prompt) if self.system_prompt else (),
            deps_type=self.deps_type,
            name=self.name,
        )

    def with_tools(self, tools: Iterable[Callable]) -> "Context":
        return replace(self, tools=tuple(tools))