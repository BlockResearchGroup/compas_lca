from dataclasses import dataclass

from typing import Any
from typing import Optional
from typing import Dict
from typing import Type
from typing import Callable
from typing import Iterable


@dataclass
class Context:
    """
    Context for configuring a single agent run.

    Optional runtime settings:
      - 'instructions': task description or guidance (prompt)
      - 'output_type': expected output schema/type
      - 'tool_resources_type': data type defining available helper tools/resources
      - 'name': name or label for this agent/run
      - 'tools': list of tool callables available to the agent
    """
    instructions: Optional[str] = None
    output_type: Optional[Type] = str
    tool_resources_type: Optional[Type] = None
    name: Optional[str] = None
    tools: Optional[Iterable[Callable]] = None

    def to_pydantic_agent_kwargs(self) -> Dict[str, Any]:
        """
        Converts context into a dictionary of keyword arguments
        accepted by 'pydantic_ai.Agent.__init__'.

        Returns:
            A dictionary with keys matching the Pydantic Agent constructor:
            - 'instructions'
            - 'output_type'
            - 'deps_type' (from 'tool_resources_type')
            - 'name'
        """
        return dict(
            output_type=self.output_type or str,
            instructions=self.instructions,
            deps_type=self.tool_resources_type,  # key must match pydantic_ai.Agent API
            name=self.name,
        )
