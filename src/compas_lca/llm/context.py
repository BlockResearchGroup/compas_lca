from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field

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
    - optional ephemeral name (name)
    - optional tools (tools)
    """

    instructions: Optional[str] = None
    system_prompt: Sequence[str] = field(default_factory=tuple) # Do I even used the system_prompt here?
    output_type: Optional[Type] = str
    deps_type: Optional[Type] = None
    name: Optional[str] = None
    tools: Optional[Iterable[Callable]] = None

    def to_agent_kwargs(self) -> Dict[str, Any]:
        return dict(
            output_type=self.output_type or str,
            instructions=self.instructions,
            system_prompt=tuple(self.system_prompt) if self.system_prompt else (),
            deps_type=self.deps_type,
            name=self.name,
        )